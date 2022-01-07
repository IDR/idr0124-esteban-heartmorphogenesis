#!/bin/bash

projectId=$1

for i in `cat segmented_files.txt`
do
	tmp=${i##*Collection/}
	imagename=${tmp%%/*}
	images=`python /uod/idr/metadata/idr-utils/scripts/annotate/find_images.py "${imagename}\.lif" Project:$projectId`
	for image in $images
	do
		if [ "$i" == "*.xz" ]
		then
			mt="application/x-tar"
		else
			mt="image/nii"
		fi
		python /uod/idr/metadata/idr-utils/scripts/annotate/attach_file.py -m $mt $i $image
	done
done
