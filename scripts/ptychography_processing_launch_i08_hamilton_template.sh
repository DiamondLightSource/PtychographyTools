#!/usr/bin/env bash

# could become a scannable. Just a place for my thoughts
#identifier=43882
identifier=44753
working_directory="/dls/i08/data/2019/cm22973-3/processing/ptychography"
data_file="/dls/i08/data/2019/cm22973-3/nexus/i08-$identifier.nxs"
log_file="/dls/tmp/ptypy_logging/$identifier_$(date +'%Y%m%d_%H%M%S').log"
data_directory="/dls/i08/data/2019/cm22973-3/nexus/"
beamline="i08"

gda_template='/dls/i08/data/2019/cm22973-3/processing/ptychography/i08-nxcxi_ptycho_no_andorinfo.yaml'
#i08_flatfield_dark_file="/dls/i08/data/2019/cm22973-3/nexus/i08-43886.nxs"
i08_flatfield_dark_file="/dls/i08/data/2019/cm22973-3/nexus/i08-44721.nxs"
i08_flatfield_dark_key="/entry/andor_addetector/data"

dawn_numprocesses=1
dawn_detector_key="/entry/andor_addetector/data"
dawn_config='/dls/i08/data/2019/cm22973-3/processing/ptychography/i08_flat_dark_correction6.nxs'

ptypy_numprocesses=80
ptypy_numgpus=4
ptypy_config="/dls/i08/data/2019/cm22973-3/processing/ptychography/Zn_battery_zocalo.json"
ptypy_version=ptycho-tools/i08
ptypy_single_threaded=False






module load dials
touch $log_file
chmod 777 $log_file
echo "logfile is: $log_file"
dlstbx.go --test \
-s identifier=$identifier \
-s working_directory=$working_directory \
-s data_file=$data_file \
-s log_file=$log_file \
-s data_directory=$data_directory \
-s beamline=$beamline \
-s gda_template=$gda_template \
-s i08_flatfield_dark_file=$i08_flatfield_dark_file \
-s i08_flatfield_dark_key=$i08_flatfield_dark_key \
-s dawn_numprocesses=$dawn_numprocesses \
-s dawn_detector_key=$dawn_detector_key \
-s dawn_config=$dawn_config \
-s ptypy_numprocesses=$ptypy_numprocesses \
-s ptypy_numgpus=$ptypy_numgpus \
-s ptypy_config=$ptypy_config \
-s ptypy_version=$ptypy_version \
-s ptypy_single_threaded=$ptypy_single_threaded \
-f /home/clb02321/PycharmProjects/PtychographyTools/scripts/zocalo_config/i08_wrap_hamilton_template.json 1234
