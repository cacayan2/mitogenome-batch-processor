for r1 in *_trim_R1.fastq.gz
do
  base=${r1%_R1.fastq.gz}
  r2=${base}_R2.fastq.gz

  echo "Running MitoZ for $base"

  mitoz assemble \
    --genetic_code 2 \
    --clade Chordata \
    --outprefix $base \
    --thread_number 8 \
    --fastq1 $r1 \
    --fastq2 $r2 \
    --run_mode 1 \
    --filter_taxa_method 1 \
    --workdir mitoz_out/$base \
    || echo "$base FAILED" >> mitoz_failed.txt

done


'''

mitoz annotate \
--fastafile animal_mt.K105.scaffolds.graph1.1.path_sequence.fasta \
--outprefix Coregonus_hoyi_after_WGA \
--genetic_code 2 \
--clade Chordata \
--species_name Coregonus_hoyi
'''