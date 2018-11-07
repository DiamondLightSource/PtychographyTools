#!/bin/bash


module load ptypy/i13-test
ptypy_script=$1


UNIQHOSTS=${TMPDIR}/machines-u
awk '{print $1 }' ${PE_HOSTFILE} | uniq > ${UNIQHOSTS}
uniqslots=$(wc -l <${UNIQHOSTS})
echo "number of uniq hosts: ${uniqslots}"
echo "running on these hosts:"
cat ${UNIQHOSTS}

typeset TMP_FILE=$( mktemp )
touch "${TMP_FILE}"
cp -p ${UNIQHOSTS} "${TMP_FILE}"
sed -e "s/$/ slots=20/" -i ${TMP_FILE}

processes=`bc <<< "$((uniqslots*20))"`
echo "Processes running are : ${processes}"

mpirun -np ${processes} --mca btl vader,self,openib -x LD_LIBRARY_PATH --hostfile ${TMP_FILE} python $ptypy_script  
