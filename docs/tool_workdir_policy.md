# Tool work directory policy

External tools should write messy/native outputs into sample-isolated work
directories:

```text
outputs/<job_id>/<stage>/work/<sample_id>/
```

Normalized pipeline outputs stay at the stage root:

```text
outputs/<job_id>/<stage>/<sample_id>.<ext>
```

Example for GetOrganelle:

```text
outputs/<job_id>/assembly/
  work/common_carp_001/
    get_org.log.txt
    *.path_sequence.fasta
    *.selected_graph.gfa
  common_carp_001.fasta
  common_carp_001.gfa
  common_carp_001.assembly.done
```
