"""Mode solver for propagating EM modes."""
from typing import Tuple

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl

from ...components.types import Numpy
from ...constants import ETA_0, C_0, fp_eps, pec_val
from .derivatives import create_d_matrices as d_mats
from .derivatives import create_s_matrices as s_mats
from .transforms import radial_transform, angled_transform


# pylint:disable=too-many-statements,too-many-branches,too-many-locals
def compute_modes(
    eps_cross,
    coords,
    freq,
    mode_spec,
    symmetry=(0, 0),
) -> Tuple[Numpy, Numpy]:
    """Solve for the modes of a waveguide cross section.

    Parameters
    ----------
    eps_cross : array_like or tuple of array_like
        Either a single 2D array defining the relative permittivity in the cross-section, or three
        2D arrays defining the permittivity at the Ex, Ey, and Ez locations of the Yee grid.
    coords : List[Numpy]
        Two 1D arrays with each with size one larger than the corresponding axis of ``eps_cross``.
        Defines a (potentially non-uniform) Cartesian grid on which the modes are computed.
    freq : float
        (Hertz) Frequency at which the eigenmodes are computed.
    mode_spec : ModeSpec
        ``ModeSpec`` object containing specifications of the mode solver.

    Returns
    -------
    Tuple[Numpy, Numpy]
        The first array gives the E and H fields for all modes, the second one give sthe complex
        effective index.
    """

    num_modes = mode_spec.num_modes
    bend_radius = mode_spec.bend_radius
    bend_axis = mode_spec.bend_axis
    angle_theta = mode_spec.angle_theta
    angle_phi = mode_spec.angle_phi
    omega = 2 * np.pi * freq
    k0 = omega / C_0

    try:
        if isinstance(eps_cross, Numpy):
            eps_xx, eps_yy, eps_zz = eps_cross
        elif len(eps_cross) == 3:
            eps_xx, eps_yy, eps_zz = [np.copy(e) for e in eps_cross]
        else:
            raise ValueError
    except Exception as e:
        print("Wrong input to mode solver pemittivity!")
        raise e

    Nx, Ny = eps_xx.shape
    N = eps_xx.size

    if coords[0].size != Nx + 1 or coords[1].size != Ny + 1:
        raise ValueError("Mismatch between 'coords' and 'esp_cross' shapes.")
    new_coords = [np.copy(c) for c in coords]

    """We work with full tensorial epsilon in mu to handle the most general cases that can
    be introduced by coordinate transformations. In the solver, we distinguish the case when
    these tensors are still diagonal, in which case the matrix for diagonalization has shape
    (2N, 2N), and the full tensorial case, in which case it has shape (4N, 4N)."""
    eps_tensor = np.zeros((3, 3, N), dtype=np.complex128)
    mu_tensor = np.zeros((3, 3, N), dtype=np.complex128)
    for dim, eps in enumerate([eps_xx, eps_yy, eps_zz]):
        eps_tensor[dim, dim, :] = eps.ravel()
        mu_tensor[dim, dim, :] = 1.0

    # Get Jacobian of all coordinate transformations. Initialize as identity (same as mu so far)
    jac_e = np.copy(mu_tensor)
    jac_h = np.copy(mu_tensor)

    if bend_radius is not None:
        new_coords, jac_e, jac_h = radial_transform(new_coords, bend_radius, bend_axis)

    if angle_theta > 0:
        new_coords, jac_e_tmp, jac_h_tmp = angled_transform(new_coords, angle_theta, angle_phi)
        jac_e = np.einsum("ij...,jp...->ip...", jac_e_tmp, jac_e)
        jac_h = np.einsum("ij...,jp...->ip...", jac_h_tmp, jac_h)

    """We also need to keep track of the transformation of the k-vector. This is
    the eigenvalue of the momentum operator assuming some sort of translational invariance and is
    different from just the transformation of the derivative operator. For example, in a bent
    waveguide, there is strictly speaking no k-vector in the original coordinates as the system
    is not translationally invariant there. However, if we define kz = R k_phi, then the
    effective index approaches that for a straight-waveguide in the limit of infinite radius. 
    Since we use w = R phi in the radial_transform, there is nothing else neede in the k transform.
    For the angled_transform, the transformation between k-vectors follows from writing the field as
    E' exp(i k_p w) in transformed coordinates, and identifying this with
    E exp(i k_x x + i k_y y + i k_z z) in the original ones."""
    kxy = np.cos(angle_theta) ** 2
    kz = np.cos(angle_theta) * np.sin(angle_theta)
    kp_to_k = np.array([kxy * np.sin(angle_phi), kxy * np.cos(angle_phi), kz])

    # Transform epsilon and mu
    jac_e_det = np.linalg.det(np.moveaxis(jac_e, [0, 1], [-2, -1]))
    jac_h_det = np.linalg.det(np.moveaxis(jac_h, [0, 1], [-2, -1]))
    eps_tensor = np.einsum("ij...,jp...->ip...", jac_e, eps_tensor)  # J.dot(eps)
    eps_tensor = np.einsum("ij...,pj...->ip...", eps_tensor, jac_e)  # (J.dot(eps)).dot(J.T)
    eps_tensor /= jac_e_det
    mu_tensor = np.einsum("ij...,jp...->ip...", jac_h, mu_tensor)
    mu_tensor = np.einsum("ij...,pj...->ip...", mu_tensor, jac_h)
    mu_tensor /= jac_h_det

    """ The forward derivative matrices already impose PEC boundary at the xmax and ymax interfaces.
    Here, we also impose PEC boundaries on the xmin and ymin interfaces through the permittivity at
    those positions, unless a PMC symmetry is specifically requested. The PMC symmetry is
    imposed by modifying the backward derivative matrices."""
    dmin_pmc = [False, False]
    if symmetry[0] != 1:
        # PEC at the xmin edge
        eps_tensor[1, 1, :Ny] = pec_val
        eps_tensor[2, 2, :Ny] = pec_val
    else:
        # Modify the backwards x derivative
        dmin_pmc[0] = True

    if Ny > 1:
        if symmetry[1] != 1:
            # PEC at the ymin edge
            eps_tensor[0, 0, ::Ny] = pec_val
            eps_tensor[2, 2, ::Ny] = pec_val
        else:
            # Modify the backwards y derivative
            dmin_pmc[1] = True

    # Primal grid steps for E-field derivatives
    dl_f = [new_cs[1:] - new_cs[:-1] for new_cs in new_coords]
    # Dual grid steps for H-field derivatives
    dl_tmp = [(dl[:-1] + dl[1:]) / 2 for dl in dl_f]
    dl_b = [np.hstack((d1[0], d2)) for d1, d2 in zip(dl_f, dl_tmp)]

    # Derivative matrices with PEC boundaries at the far end and optional pmc at the near end
    der_mats_tmp = d_mats((Nx, Ny), dl_f, dl_b, dmin_pmc)

    # PML matrices; do not impose PML on the bottom when symmetry present
    dmin_pml = np.array(symmetry) == 0
    pml_mats = s_mats(omega, (Nx, Ny), mode_spec.num_pml, dl_f, dl_b, dmin_pml)

    # Add the PML on top of the derivatives; normalize by k0 to match the EM-possible notation
    der_mats = [Smat.dot(Dmat) / k0 for Smat, Dmat in zip(pml_mats, der_mats_tmp)]

    # Determine initial guess value for the solver in transformed coordinates
    if mode_spec.target_neff is None:
        eps_physical = np.array(eps_cross)
        eps_physical = eps_physical[np.abs(eps_physical) < np.abs(pec_val)]
        n_max = np.sqrt(np.max(np.abs(eps_physical)))
        target = n_max
    else:
        target = mode_spec.target_neff
    target_neff_p = target / np.linalg.norm(kp_to_k)

    # Solve for the modes
    E, H, neff, keff = solver_em(eps_tensor, mu_tensor, der_mats, num_modes, target_neff_p)

    # Reorder if needed
    if mode_spec.sort_by != "largest_neff":
        if mode_spec.sort_by == "te_fraction":
            sort_int = np.sum(np.abs(E[0]) ** 2, axis=0) / np.sum(np.abs(E[:2]) ** 2, axis=(0, 1))
        elif mode_spec.sort_by == "tm_fraction":
            sort_int = np.sum(np.abs(E[1]) ** 2, axis=0) / np.sum(np.abs(E[:2]) ** 2, axis=(0, 1))
        sort_inds = np.argsort(sort_int)[::-1]
        E = E[..., sort_inds]
        H = H[..., sort_inds]
        neff = neff[..., sort_inds]
        keff = keff[..., sort_inds]

    # Transform back to original axes, E = J^T E'
    E = np.sum(jac_e[..., None] * E[:, None, ...], axis=0)
    E = E.reshape((3, Nx, Ny, 1, num_modes))
    H = np.sum(jac_h[..., None] * H[:, None, ...], axis=0)
    H = H.reshape((3, Nx, Ny, 1, num_modes))
    neff = neff * np.linalg.norm(kp_to_k)

    fields = np.stack((E, H), axis=0)

    return fields, neff + 1j * keff


def solver_em(eps_tensor, mu_tensor, der_mats, num_modes, neff_guess):
    """Solve for the electromagnetic modes of a system defined by in-plane permittivity and
    permeability and assuming translational invariance in the normal direction.

    Parameters
    ----------
    eps_tensor : np.ndarray
        Shape (3, 3, N), the permittivity tensor at every point in the plane.
    mu_tensor : np.ndarray
        Shape (3, 3, N), the permittivity tensor at every point in the plane.
    der_mats : List[scipy.sparse.csr_matrix]
        The sparce derivative matrices dxf, dxb, dyf, dyb, including the PML.
    num_modes : int
        Number of modes to solve for.
    neff_guess : float
        Initial guess for the effective index.

    Returns
    -------
    E : np.ndarray
        Electric field of the eigenmodes, shape (3, N, num_modes).
    H : np.ndarray
        Magnetic field of the eigenmodes, shape (3, N, num_modes).
    neff : np.ndarray
        Real part of the effective index, shape (num_modes, ).
    keff : np.ndarray
        Imaginary part of the effective index, shape (num_modes, ).
    """

    off_diagonals = (np.ones((3, 3)) - np.eye(3)).astype(bool)
    eps_offd = np.abs(eps_tensor[off_diagonals])
    mu_offd = np.abs(mu_tensor[off_diagonals])
    if np.any(eps_offd > 1e-6) or np.any(mu_offd > 1e-6):
        return solver_tensorial(eps_tensor, mu_tensor, der_mats, num_modes, neff_guess)

    return solver_diagonal(eps_tensor, mu_tensor, der_mats, num_modes, neff_guess)


def solver_diagonal(eps, mu, der_mats, num_modes, neff_guess):
    """EM eigenmode solver assuming ``eps`` and ``mu`` are diagonal everywhere."""

    N = eps.shape[-1]

    # Unpack eps, mu and derivatives
    eps_xx = eps[0, 0, :]
    eps_yy = eps[1, 1, :]
    eps_zz = eps[2, 2, :]
    mu_xx = mu[0, 0, :]
    mu_yy = mu[1, 1, :]
    mu_zz = mu[2, 2, :]
    dxf, dxb, dyf, dyb = der_mats

    # Compute the matrix for diagonalization
    inv_eps_zz = sp.spdiags(1 / eps_zz, [0], N, N)
    inv_mu_zz = sp.spdiags(1 / mu_zz, [0], N, N)
    p11 = -dxf.dot(inv_eps_zz).dot(dyb)
    p12 = dxf.dot(inv_eps_zz).dot(dxb) + sp.spdiags(mu_yy, [0], N, N)
    p21 = -dyf.dot(inv_eps_zz).dot(dyb) - sp.spdiags(mu_xx, [0], N, N)
    p22 = dyf.dot(inv_eps_zz).dot(dxb)
    q11 = -dxb.dot(inv_mu_zz).dot(dyf)
    q12 = dxb.dot(inv_mu_zz).dot(dxf) + sp.spdiags(eps_yy, [0], N, N)
    q21 = -dyb.dot(inv_mu_zz).dot(dyf) - sp.spdiags(eps_xx, [0], N, N)
    q22 = dyb.dot(inv_mu_zz).dot(dxf)

    pmat = sp.bmat([[p11, p12], [p21, p22]])
    qmat = sp.bmat([[q11, q12], [q21, q22]])
    mat = pmat.dot(qmat)

    # Call the eigensolver. The eigenvalues are -(neff + 1j * keff)**2
    vals, vecs = solver_eigs(mat, num_modes, guess_value=-(neff_guess**2))
    if vals.size == 0:
        raise RuntimeError("Could not find any eigenmodes for this waveguide")
    vre, vim = -np.real(vals), -np.imag(vals)

    # Sort by descending real part
    sort_inds = np.argsort(vre)[::-1]
    vre = vre[sort_inds]
    vim = vim[sort_inds]
    vecs = vecs[:, sort_inds]

    # Real and imaginary part of the effective index
    neff = np.sqrt(vre / 2 + np.sqrt(vre**2 + vim**2) / 2)
    keff = vim / 2 / (neff + 1e-10)

    # Field components from eigenvectors
    Ex = vecs[:N, :]
    Ey = vecs[N:, :]

    # Get the other field components
    h_field = qmat.dot(vecs)
    Hx = h_field[:N, :] / (1j * neff - keff)
    Hy = h_field[N:, :] / (1j * neff - keff)
    Hz = inv_mu_zz.dot((dxf.dot(Ey) - dyf.dot(Ex)))
    Ez = inv_eps_zz.dot((dxb.dot(Hy) - dyb.dot(Hx)))

    # Bundle up
    E = np.stack((Ex, Ey, Ez), axis=0)
    H = np.stack((Hx, Hy, Hz), axis=0)

    # Return to standard H field units (see CEM notes for H normalization used in solver)
    H *= -1j / ETA_0

    return E, H, neff, keff


def solver_tensorial(eps, mu, der_mats, num_modes, neff_guess):
    """EM eigenmode solver assuming ``eps`` or ``mu`` have off-diagonal elements."""

    N = eps.shape[-1]
    dxf, dxb, dyf, dyb = der_mats

    # Compute all blocks of the matrix for diagonalization
    inv_eps_zz = sp.spdiags(1 / eps[2, 2, :], [0], N, N)
    inv_mu_zz = sp.spdiags(1 / mu[2, 2, :], [0], N, N)
    axax = -dxf.dot(sp.spdiags(eps[2, 0, :] / eps[2, 2, :], [0], N, N)) - sp.spdiags(
        mu[1, 2, :] / mu[2, 2, :], [0], N, N
    ).dot(dyf)
    axay = -dxf.dot(sp.spdiags(eps[2, 1, :] / eps[2, 2, :], [0], N, N)) + sp.spdiags(
        mu[1, 2, :] / mu[2, 2, :], [0], N, N
    ).dot(dxf)
    axbx = -dxf.dot(inv_eps_zz).dot(dyb) + sp.spdiags(
        mu[1, 0, :] - mu[1, 2, :] * mu[2, 0, :] / mu[2, 2, :], [0], N, N
    )
    axby = dxf.dot(inv_eps_zz).dot(dxb) + sp.spdiags(
        mu[1, 1, :] - mu[1, 2, :] * mu[2, 1, :] / mu[2, 2, :], [0], N, N
    )
    ayax = -dyf.dot(sp.spdiags(eps[2, 0, :] / eps[2, 2, :], [0], N, N)) + sp.spdiags(
        mu[0, 2, :] / mu[2, 2, :], [0], N, N
    ).dot(dyf)
    ayay = -dyf.dot(sp.spdiags(eps[2, 1, :] / eps[2, 2, :], [0], N, N)) - sp.spdiags(
        mu[0, 2, :] / mu[2, 2, :], [0], N, N
    ).dot(dxf)
    aybx = -dyf.dot(inv_eps_zz).dot(dyb) + sp.spdiags(
        -mu[0, 0, :] + mu[0, 2, :] * mu[2, 0, :] / mu[2, 2, :], [0], N, N
    )
    ayby = dyf.dot(inv_eps_zz).dot(dxb) + sp.spdiags(
        -mu[0, 1, :] + mu[0, 2, :] * mu[2, 1, :] / mu[2, 2, :], [0], N, N
    )
    bxbx = -dxb.dot(sp.spdiags(mu[2, 0, :] / mu[2, 2, :], [0], N, N)) - sp.spdiags(
        eps[1, 2, :] / eps[2, 2, :], [0], N, N
    ).dot(dyb)
    bxby = -dxb.dot(sp.spdiags(mu[2, 1, :] / mu[2, 2, :], [0], N, N)) + sp.spdiags(
        eps[1, 2, :] / eps[2, 2, :], [0], N, N
    ).dot(dxb)
    bxax = -dxb.dot(inv_mu_zz).dot(dyf) + sp.spdiags(
        eps[1, 0, :] - eps[1, 2, :] * eps[2, 0, :] / eps[2, 2, :], [0], N, N
    )
    bxay = dxb.dot(inv_mu_zz).dot(dxf) + sp.spdiags(
        eps[1, 1, :] - eps[1, 2, :] * eps[2, 1, :] / eps[2, 2, :], [0], N, N
    )
    bybx = -dyb.dot(sp.spdiags(mu[2, 0, :] / mu[2, 2, :], [0], N, N)) + sp.spdiags(
        eps[0, 2, :] / eps[2, 2, :], [0], N, N
    ).dot(dyb)
    byby = -dyb.dot(sp.spdiags(mu[2, 1, :] / mu[2, 2, :], [0], N, N)) - sp.spdiags(
        eps[0, 2, :] / eps[2, 2, :], [0], N, N
    ).dot(dxb)
    byax = -dyb.dot(inv_mu_zz).dot(dyf) + sp.spdiags(
        -eps[0, 0, :] + eps[0, 2, :] * eps[2, 0, :] / eps[2, 2, :], [0], N, N
    )
    byay = dyb.dot(inv_mu_zz).dot(dxf) + sp.spdiags(
        -eps[0, 1, :] + eps[0, 2, :] * eps[2, 1, :] / eps[2, 2, :], [0], N, N
    )

    mat = sp.bmat(
        [
            [axax, axay, axbx, axby],
            [ayax, ayay, aybx, ayby],
            [bxax, bxay, bxbx, bxby],
            [byax, byay, bybx, byby],
        ]
    )

    # Call the eigensolver. The eigenvalues are 1j * (neff + 1j * keff)
    vals, vecs = solver_eigs(mat, num_modes, guess_value=1j * neff_guess)
    if vals.size == 0:
        raise RuntimeError("Could not find any eigenmodes for this waveguide")
    # Real and imaginary part of the effective index
    neff, keff = np.imag(vals), -np.real(vals)

    # Sort by descending real part
    sort_inds = np.argsort(neff)[::-1]
    neff = neff[sort_inds]
    keff = keff[sort_inds]
    vecs = vecs[:, sort_inds]

    # Field components from eigenvectors
    Ex = vecs[:N, :]
    Ey = vecs[N : 2 * N, :]
    Hx = vecs[2 * N : 3 * N, :]
    Hy = vecs[3 * N :, :]

    # Get the other field components
    hxy_term = (-mu[2, 0, :] * Hx.T - mu[2, 1, :] * Hy.T).T
    Hz = inv_mu_zz.dot(dxf.dot(Ey) - dyf.dot(Ex) + hxy_term)
    exy_term = (-eps[2, 0, :] * Ex.T - eps[2, 1, :] * Ey.T).T
    Ez = inv_eps_zz.dot(dxb.dot(Hy) - dyb.dot(Hx) + exy_term)

    # Bundle up
    E = np.stack((Ex, Ey, Ez), axis=0)
    H = np.stack((Hx, Hy, Hz), axis=0)

    # Return to standard H field units (see CEM notes for H normalization used in solver)
    # The minus sign here is suspicious, need to check how modes are used in Mode objects
    H *= -1j / ETA_0

    return E, H, neff, keff


def solver_eigs(mat, num_modes, guess_value=1.0):
    """Find ``num_modes`` eigenmodes of ``mat`` cloest to ``guess_value``.

    Parameters
    ----------
    mat : scipy.sparse matrix
        Square matrix for diagonalization.
    num_modes : int
        Number of eigenmodes to compute.
    guess_value : float, optional
    """

    values, vectors = spl.eigs(mat, k=num_modes, sigma=guess_value, tol=fp_eps)
    return values, vectors
