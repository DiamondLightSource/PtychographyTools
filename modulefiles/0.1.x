#%Module1.0#####################################################################
##
## ptycho-tools modulefile
##
proc ModulesHelp { } {
    global version

    puts stderr "\tLoads version $version of ptycho-tools"
    puts stderr "\n\tptycho-tools contains wrappers for ptypy within Diamond"
}

# this is the name of the module
set version 0.1.x

module-whatis "loads ptychotools package version $version"

if { ! [is-loaded global/directories] } {
    module load global/directories
}

module load ptypy/stable

set PTYCHOTOOLS_PATH /home/kbp43231/22/PtychographyTools
# you need to set this

prepend-path PYTHONPATH $PTYCHOTOOLS_PATH
puts stdout "export PATH=$PTYCHOTOOLS_PATH/scripts:\$PATH;"

setenv PTYCHOTOOLS_VERSION ptycho-tools/$version

if { [info exists env(BEAMLINE)] } {
    puts stderr "We are version $version on beamline: $env(BEAMLINE)"
    set-alias "ptypy_mpi" "ptychotools.ptypy_launcher -c /dls_sw/apps/ptychography_tools/cluster_configurations/$env(BEAMLINE).txt"
    # won't happen on the cluster
}
