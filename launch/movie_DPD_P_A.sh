#! /bin/bash

if [[ "$DATA" == "" ]]; then
	echo "No data name submitted."
	exit 0
fi

export DATA=$DATA

export INITIAL_FRAME=${INITIAL_FRAME-0}
export FRAME_PERIOD=${FRAME_PERIOD-1}
export FRAME_MAXIMUM=${FRAME_MAXIMUM-1000}

. /home/yketa/exponents.sh # exporting letters expressions and float conversion functions
MOV_PAR=mov_I$(float_to_letters $INITIAL_FRAME)_M$(float_to_letters $FRAME_MAXIMUM)_P$(float_to_letters $FRAME_PERIOD)

mkdir -p /home/yketa/hoomd/colmig_DPD_P_A/data/${DATA}/out
output_file=/home/yketa/hoomd/colmig_DPD_P_A/data/${DATA}/out/${MOV_PAR}.out
> $output_file

sbatch --job-name=${MOV_PAR}_${DATA} <<EOF
#!/bin/bash
#SBATCH --partition=gpu
#SBATCH --gres=gpu:k80:1
#SBATCH --output /home/yketa/hoomd/colmig_DPD_P_A/sub/out/${MOV_PAR}_${DATA}.%j.out
#SBATCH --ntasks-per-node 1

/bin/bash /home/yketa/bin/_colmig_DPD_P_A_makemovie >> $output_file
EOF

