#!/bin/bash

mkdir -p new
for r1 in trimmed_fastq/*_trim_R1.fastq.gz
do
  base=$(basename "$r1" _trim_R1.fastq.gz)
  r2="trimmed_fastq/${base}_trim_R2.fastq.gz"

  get_organelle_from_reads.py \
    -1 "$r1" \
    -2 "$r2" \
    -F animal_mt \
    -R 10 \
    -k 21,45,65,85,105 \
    -t 8 \
    -o new/${base}_mt_retry
done

'''

get_organelle_from_reads.py -1 Etheostoma_blennioides_blennioides_after_WGA_GAATGTGTTG-ACGGAGATGG_L004_trim_R1.fastq -2 Etheostoma_blennioides_blennioides_after_WGA_GAATGTGTTG-ACGGAGATGG_L004_trim_R2.fastq -R 10 -k 21,45,65,85,105 -F animal_mt -o get


get_organelle_from_reads.py \
    -1 "Extraction_Blank_after_WGA_after_WGA_AGTAACACGG-GCAAGCACCT_L004_trim_R1.fastq.gz" \
    -2 "Extraction_Blank_after_WGA_after_WGA_AGTAACACGG-GCAAGCACCT_L004_trim_R2.fastq.gz" \
    -F animal_mt \
    -R 10 \
    -k 21,45,65,85,105 \
    -t 8 \
    -o get \
    --overwrite

get_organelle_from_reads.py \
    -1 "Etheostoma_blennioides_blennioides_before_WGA_AAGGTGGTTG-CCGGTCATAC_L004_trim_R1.fastq.gz" \
    -2 "Etheostoma_blennioides_blennioides_before_WGA_AAGGTGGTTG-CCGGTCATAC_L004_trim_R2.fastq.gz" \
    -F animal_mt \
    -R 10 \
    -k 21,45,65,85,105 \
    -t 4 \
    -o get/Etheostoma_blennioides_blennioides_before_WGA

get_organelle_from_reads.py \
    -1 "Salmo_trutta_before_WGA_GTGTCGGATT-AAGCGGAGAA_L004_trim_R1.fastq.gz" \
    -2 "Salmo_trutta_before_WGA_GTGTCGGATT-AAGCGGAGAA_L004_trim_R2.fastq.gz" \
    -F animal_mt \
    -R 10 \
    -k 21,45,65,85,105 \
    -t 8 \
    -o get/Salmo_trutta_before_WGA
'''
   
