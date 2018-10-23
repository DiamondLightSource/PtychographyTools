timestamp=$(date +"%Y%m%d_%H%M%S")
logpath=/dls/tmp/ptypy_logging/i13_log_$timestamp.txt
touch $logpath

module load global/cluster >> $logpath 
json_file=$1
identifier=$2
output_folder=$3

echo "The arguments passed in the launcher are:$@" >> $logpath

qsub -jsv /dls_sw/apps/sge/common/JSVs/savu.pl -j y -pe openmpi 20 -l exclusive -l infiniband -l gpu=2 -l gpu_arch=Pascal -q high.q@@com14 -P tomography -o $logpath -e $logpath /dls_sw/apps/ptypy/i13_test/cluster_scripts/ptypy_mpijob_i14.sh $json_file $identifier $output_folder $logpath >> $logpath
