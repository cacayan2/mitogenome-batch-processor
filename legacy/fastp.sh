
'''
#!/bin/bash
#making two directories
#!/bin/bash
set -euo pipefail

# make output directories
mkdir -p trimmed_fastq fastq_reports

# loop through all R1 fastq files
for r1 in raw_fastq/*_R1_001.fastq.gz
do
    base=$(basename "$r1" _R1_001.fastq.gz)
    r2="raw_fastq/${base}_R2_001.fastq.gz"

    fastp \
        -i "$r1" \
        -I "$r2" \
        -o "trimmed_fastq/${base}.trim_R1.fastq.gz" \
        -O "trimmed_fastq/${base}.trim_R2.fastq.gz" \
        --detect_adapter_for_pe \
        --disable_quality_filtering \
        --disable_length_filtering \
        --thread 10 \
        --html "fastq_reports/${base}.fastp.html" \
        --json "fastq_reports/${base}.fastp.json"
done
'''
#!/bin/bash
set -euo pipefail
#make two folder
mkdir -p trimmed_fastq fastq_reports


#loop through all R1 fastq files
for r1 in raw_fastq/*_R1_001.fastq.gz
do
base=$(basename "$r1" _R1_001.fastq.gz)
r2="raw_fastq/${base}_R2_001.fastq.gz"

outR1="trimmed_fastq/${base}_trim_R1.fastq.gz"
outR2="trimmed_fastq/${base}_trim_R2.fastq.gz"
report_html="fastq_reports/${base}.fastp.html"
report_json="fastq_reports/${base}.fastp.json"
'''
# Check if files exist and are non-empty
if [[ -s "$outR1" && -s "$outR2" && -s "$report_html" && -s "$report_json" ]]; then
echo "Skipping ${base} (already processed & complete)"
continue
fi

echo "Running fastp for ${base} ..."
'''
fastp \
-i "$r1" \
-I "$r2" \
-o "$outR1" \
-O "$outR2" \
--detect_adapter_for_pe \
--disable_quality_filtering \
--disable_length_filtering \
--thread 8 \
--html "$report_html" \
--json "$report_json"
done

echo " Done!"