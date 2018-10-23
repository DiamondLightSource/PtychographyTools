#!/bin/bash

json_file=$1
identifier=$2
output_folder=$3
logpath=$4

echo "We are in the MPI job" >> $logpath
module load ptypy/i13-test >> $logpath
echo "The json file is $json_file" >> $logpath
echo "The identifier is $identifier" >> $logpath
echo "The output folder is $output_folder" >> $logpath


UNIQHOSTS=${TMPDIR}/machines-u
awk '{print $1 }' ${PE_HOSTFILE} | uniq > ${UNIQHOSTS}
uniqslots=$(wc -l <${UNIQHOSTS})
echo "number of uniq hosts: ${uniqslots}" >> $logpath
echo "running on these hosts:" >> $logpath
cat ${UNIQHOSTS} >>$logpath

typeset TMP_FILE=$( mktemp )
touch "${TMP_FILE}"
cp -p ${UNIQHOSTS} "${TMP_FILE}"
sed -e "s/$/ slots=20/" -i ${TMP_FILE}

processes=`bc <<< "$((uniqslots*20))"`
echo "Processes running are : ${processes}" >> $logpath

mpirun -np ${processes} --mca btl vader,self,openib -x LD_LIBRARY_PATH --hostfile ${TMP_FILE} ptypy.run $json_file -I $identifier -O $output_folder -P 0 >> $logpath
