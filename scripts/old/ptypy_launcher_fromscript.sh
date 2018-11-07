module load global/cluster
ptypy_script=$1

qsub -jsv /dls_sw/apps/sge/common/JSVs/savu.pl -j y -pe openmpi 80 -l exclusive -l infiniband -l gpu=2 -l gpu_arch=Pascal -q high.q@@com14 /dls_sw/apps/ptypy/i13_test/cluster_scripts/ptypy_mpijob_fromscript.sh $ptypy_script
