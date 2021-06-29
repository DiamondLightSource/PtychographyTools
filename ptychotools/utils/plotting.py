import h5py, os
import numpy as np
import imageio
import matplotlib.pyplot as plt
import matplotlib.colors as colors


def make_spectro_scan_movie(basepath, prefix, radius=0.4):
    in_phase    = basepath + "/" + prefix + "phase.nxs"
    in_odensity = basepath + "/" + prefix + "optical_density.nxs"
    in_probe_intensity = basepath + "/" + prefix + "probe_intensity.nxs"
    out_movie = basepath + "/" + prefix + "movie.mp4"

    fp = h5py.File(in_phase, "r")
    fo = h5py.File(in_odensity, "r")
    fi = h5py.File(in_probe_intensity, "r")

    eng = fp["entry1/Counter1/photon_energy"][:]
    N = len(eng)

    phase = fp["entry1/Counter1/data"][:]
    odensity = fo["entry1/Counter1/data"][:]
    probeint = fi["entry1/Counter1/data"][:]

    ny,nx = phase[0].shape
    XX,YY = np.meshgrid(np.arange(nx) - nx//2, np.arange(ny) - ny//2)
    W = np.sqrt(XX**2 + YY**2) < (radius * (nx+ny) / 4)

    phase_spectrum = phase[:,W].mean(axis=1)
    odensity_spectrum = odensity[:,W].mean(axis=1)
    
    print("Creating temporary plots")
    for i in range(N):
        fig = plt.figure(figsize=(16,12), dpi=100)
        axo = fig.add_subplot(231)
        axp = fig.add_subplot(232)
        axi = fig.add_subplot(233)
        ax1 = fig.add_subplot(212)
        ax2 = ax1.twinx()
        axo.axis('off')
        axo.set_title("Optical density (%.1f eV)" %eng[i])
        axo.imshow(odensity[i], vmin=-1.5, vmax=1.5, cmap='gray', interpolation='none')
        axo.add_patch(plt.Circle((ny//2,nx//2),radius *(nx+ny)/4, fill=0, color='tab:blue'))
        axp.axis('off')
        axp.set_title("Phase (%.1f eV)" %eng[i])
        axp.imshow(phase[i], vmin=-1, vmax=0, cmap='gray', interpolation='none')
        axp.add_patch(plt.Circle((ny//2,nx//2),radius *(nx+ny)/4, fill=0, color='tab:orange'))
        axi.axis('off')
        axi.set_title("Probe intensity (%.1f eV)" %eng[i])
        axi.imshow(probeint[i], cmap='inferno', interpolation='none', norm=colors.LogNorm(1,1e5))
        ax1.plot(eng, odensity_spectrum, label="Opt. density", color="tab:blue")
        ax1.plot(eng[i], odensity_spectrum[i], marker="o", color="tab:blue") 
        ax2.plot(eng, phase_spectrum, label="Phase", color="tab:orange")
        ax2.plot(eng[i], phase_spectrum[i], marker="o", color="tab:orange")
        ax1.set_ylim(-0.0, 1.5)
        ax2.set_ylim(-1.5, 0.0)
        ax1.set_xlabel("Photon energy [eV]")
        ax1.set_ylabel("Opt. density")
        ax2.set_ylabel("Phase")
        ax1.legend(frameon=0, loc=2)
        ax2.legend(frameon=0, loc=4)
        fig.savefig(basepath + "/.tmp_%04d.png" %i)
        plt.close(fig)
        
    print("Creating a move and save it to ", out_movie)
    imageio.mimwrite(out_movie, [imageio.imread(basepath + "/.tmp_%04d.png" %i) for i in range(N)], format="mp4", fps=5)
    [os.remove(basepath + "/.tmp_%04d.png" %i) for i in range(N)]
