```{=typst}
#set page(margin: (x:0.5in, y:0.5in))
#show link: set text(fill: blue)
```

```{=typst}
#align(center)[
```
# Mitochondrial Genome Processing Pipeline
## Emil Cacayan
```{=typst}
]
```
---

## Project Objective 
The goal of this project is the development of a pipeline which will batch process and assemble raw reads of mitochondrial dna into completed mitogenomes that comprise a reference database for fish species along the Fox River. This reference database would ideally then be published to NCBI GenBank and compiled into a microbiology resource announcement. 

For the creation of this pipeline, focus will be on documentation, reproducibility, error handling and logging, determination of data fidelity, and test-driven design. Progress of this project will be saved and tracked on GitHub (linked below): 

```{=typst}
#align(center)[
```
- [Repository](https://github.com/cacayan2/mitogenome-batch-processor.git)
- [Project](https://github.com/users/cacayan2/projects/3/views/1)
```{=typst}
]
```

---

## Background and Motivation
One of the most difficult tasks that ecologists must overcome is tracking distribution of species of interest, particularly for those in freshwater ecosystems. Traditional surveys typically require catching fish, netting insects, sampling fixed species such as mussels, and sending biologists into the field for these non-trivial and time intensive tasks (Schilling et al., 2022). These surveys are infrequent and expensive, and particularly for conservation agencies who have a vested interest in the distribution of species, their potential to become threatened, and an empirical determination of environmental impacts of urban activity, this information can be quite valuable. One of the ways that biologists have overcome this bottleneck is via metabarcoding. 

DNA barcoding was a technique introduced in 2003 by Paul Herbert who proposed that using a short standardized DNA sequence (often the mitochondrial cytocrome c oxidase subunit I gene) as a "barcode" that could be used to identify species (Mohammed et al., 2017). This barcode could be matched to a reference database in order to quickly determine the species the mitogene belonged to. Mitochondrial DNA has a few distinct advantages over using genomic DNA for species identification:

- Easier to detect in degraded samples
    + mtDNA is present in high copy number per cell compared to genomic DNA (Merheb et al., 2019; Mohammed et al., 2017)
    + Mitochondrial genomes are small, circular rings of DNA physically packaged inside the mitochondria, offering additional protection against degradation (Merheb et al., 2019; Mohammed et al., 2017)
- Conserved enough to amplify easily (Singh et al., 2017)
- Variable enough to distinguish between species (Singh et al., 2017; Mohammed et al., 2017)

In the late 2000's, next-generation sequencing allowed for higher-fidelity higher-throughput samples of environmental samples of DNA (called eDNA) (Yoon et al., 2025). This allows for the simultaneous sequencing of entire ecological populations contained within a single ecosystems. This DNA could be barcoded against a reference database, and became known as metabarcoding and was applied to soils, lakes, forests, and gut microbiota. 

The Stuart Lab is interested in studying the distribution of freshwater fish along the length of the Fox River (Illinois River Tributary), which flows southwest from southeastern Wisconsin down into northeastern Illinois. This 202-mile-long river originates at Colgate, Wisconsin and crosses into northern Illinois to form the famous Fox Chain O'Lakes, and continues to meander south until it joins the Illinois River at Ottawa, Illinois (Fox River Watershed | Lake County, IL, 2023). 

Ecologically, this river serves a few essential functions:

**1. High-Density Interaction Corridor for Urban Wildlife:**

<br><small>This river is highly salient to its respective ecological community as it serves a niche as a vital ecological oasis inside one of the most highly urbanized and agricultural regions in the United States. This river cuts through the densely populated Chicago suburban collar known as the Fox Valley (Fox River, 2025). The river runs through key portions of forest preserves in the Northwest Suburbs of Illinois (McHenry, Kane, and Will counties specifically) and allows terrestrial and semi-acquatic wildlife (river otters, minks, foxes, and deer) to migrate, forage, and breed without being trapped by suburban sprawl (Fox River, 2025). The river also serves as a massive regional sponge, capturing stormwater runoff to prevent flooding in the larger Chicago metro area and surrounding suburbs (Baldwin, 2026). </br></small>

**2. Refuge for Threatened Freshwater Mussels:**

<br><small>The Illinois Fox River basin is globally significant for its biodiversity of native fresthwater mussels (supporting 24 to 32 distinct species) (Schanzle et al., 2004). Millions of these mussels act as a natural filter for bacteria and algae (up to 10 gallons of water a day) cleaning the water column (Black et al., 2017). The reproductive cycle of these species are quite complex, many requiring larvae to attach to the gills of native fish to grow (Rock et al., 2022). The Fox River provides the multi-species environment for this fragile paradigm to survive - many of these fish species being threatened (such as the Plain Pocketbook, Elktoe, and White Heelsplitter) (Altenritter & Casper, 2018; Shasteen et al., 2013; Limpers 2022). </br></small>

**3. Native Fishery:**

<br><small> The Fox River is a premier warmwater habitat that hosts nearly 100 native fish (State of the Fox River Report 2003, n.d.). It supports robust populations of apex game fish such as Smallmouth Bass, Flathead Catfish, and Walleye, which keep smaller fish populations healthy and balanced (State of the Fox River Report 2003, n.d.). Feeding streams that branch off the main river (namely Nippersink Creek and Ferson Creek) act as clean, high-quality spawnning grounds where sensitive species lay eggs away from the main river (State of the Fox River Report 2003, n.d.). </br></small>

One of the largest ecological shifts currently occurring in the river is a transition that is largely being facilitated by man. Obsolete industrial dams fragmented the Illinois portion of the river into disconnected pools, preventing migration to upstream spawning creeks, lowering oxygen levels, and caused heavy siltation that suffocated mussel beds (Carpentersville Dam Removal Project - Resource Environmental Solutions, LLC, 2025). While removal of these dams allows for a transition to a free-flowing aquatic highway, it is important to track pre-removal and post-removal changes in the ecological distribution of different species present within the Fox River, as a major concern of residents along the Fox River is fish loss and alleviating this concern is a major goal of ecological conservation groups such as Friends of the Fox River (Y. Stuart, Research Proposal). 

Metabarcoding would allow for a nearly synchronous view of the state of an ecological population and trend of population distribution over time with minimal logistical and financial overhead, and would be directly applicable to the study of fish population following dam removal in the Fox River. This method could be further applied to other methods, such as studying the effects of urban and agricultural development and runoff, determination of threatened or endangered species, and the studying of fish migratory patterns. But the one caveat to metabarcoding is: **any metabarcoding workflow is only as good as its reference database.**

The goal of the development of this pipeline is to create a reference database of mitochondrial genomes obtained from next generation sequencing of eDNA collected along the Fox River (covering ~140 fish species) (Y. Stuart, Research Proposal). This database, if completed, would be one of the most thorough eDNA metabarcoding reference databases in the world. Eventually, all mitogenomes will be accessionged to NCBI's GenBank repository, this database will be available for use by researchers and managers throughout the Great Lakes, Mississippi River, and beyond to support conservation and restoration projects (Y. Stuart, Research Proposal). 

---

```{=typst}
#pagebreak()
```

## Initial Goals
```{=typst}
#rect(fill: luma(245), width: 100%, inset: 15pt)[
```
### Goal 1: Understand Existing Workflow
- Review funded proposal documentation and Richa Patel's thesis workflow
- Examine published mitogenome announcement papers
- Identify required inputs, outputs, and manual steps

**Deliverable:**

- A design plan documenting the current process and architectural design record containing current tools, strengths, limitations, etc.

**Notes:** Current workflow looks like `fastp` → `GetOrganelle` → `MitoZ`. A complete diagrammatic workflow of Richa Patel's pipeline can be found [here](https://ecommons.luc.edu/cgi/viewcontent.cgi?article=2463&context=ures).
```{=typst}
]
```

```{=typst}
#rect(fill: luma(245), width: 100%, inset: 15pt)[
```
### Goal 2: Development of Reproducible Processing Pipeline

Develop scripts that can: 

- Import raw data
- Organize project structure
- Perform QC
- Generate standardized outputs
- Perform robust logging and error reporting

**Deliverable:** 

- Version-controlled pipeline repository

**Note:** Considering using Nextflow or Snakemake to automate the pipeline. Also investigate seed sequences required for different tools in pipeline. 
```{=typst}
]
```

```{=typst}
#rect(fill: luma(245), width: 100%, inset: 15pt)[
```
### Goal 3: Automate Genome Statistics Reporting

Automatically calculate genome length, GC content, gene counts, coverage metrics, other statistics and visualize as a table. 

**Deliverable:**

- Automatically generated summary table of relevant statistics
```{=typst}
]
```

```{=typst}
#rect(fill: luma(245), width: 100%, inset: 15pt)[
```
### Goal 4: Automate Genome Statistics Reporting

Investigate automated generation of: 

- Circularized mitochondrial genome maps
- Gene organization figures
- QC visualizations

**Deliverable:**

- Publication-ready figures generated from pipeline
```{=typst}
]
```

```{=typst}
#rect(fill: luma(245), width: 100%, inset: 15pt)[
```
### Goal 5: Automate Phylogenetic Analysis

Develop procedures for: 
- Reference sequence retrieval
- Sequence alignment
- Tree construction
- Figure generation

**Deliverable:**
- Reproducible phylogenetic analysis
```{=typst}
]
```

```{=typst}
#rect(fill: luma(245), width: 100%, inset: 15pt)[
```
### Goal 6: Automated Reported

Generate standardized Markdown reports documenting:

- Genome statistics
- Figures
- Phylogenetic results
- Submission metadata

**Deliverable:**

- Automatically generated report for each species
```{=typst}
]
```
---

## Proposed Development Strategy
### Phase 1 - Literature and Workflow Review
- Understand dataset and current methodology
- Identify opportunities for improvement

### Phase 2 - Pipeline Prototyping
- Build core scripts
- Test on small number of species

### Phase 3 - Validation
- Compare outputs against previously completed analysis
- Verify reproducibility
- Draft, finalize, and submit midsemester report

### Phase 4 - Scaling
- Process larger batches of species, identify areas of improvement for automation and runtime

### Phase 5 - Documentation
- Finalize [`README.md`](https://github.com/cacayan2/mitogenome-batch-processor.git) as a user guide, including
    + Installation instructions
    + Overall pipeline documentation

### Phase 6 - Manuscript Creation
- Finalize creation of manuscript and presentation. 

---

## Expected Outcomes
- Reproducible mitrochondrial genome processing pipeline
- Reduced manual effort for future projects
- Standardized outputs across species
- Automated report generation
- Foudnation for large-scale mitogenome processing

---

## Questions for Discussion
- Which portions of the current workflow are considered highest priority to automate?
- What software tools are currently utilized for the current workflow? Are there alternatives? 
- Are there existing datasets that can be utilized for validation?

---

## References
Altenritter, M., & Casper, A. F. (2018, September 24). Evaluating the potential responses of native fish and mussels to proposed separation of Lake Michigan from the Illinois River Waterway at Brandon Road Lock and Dam. https://www.researchgate.net/publication/327845663_Evaluating_the_potential_responses_of_native_fish_and_mussels_to_proposed_separation_of_Lake_Michigan_from_the_Illinois_River_Waterway_at_Brandon_Road_Lock_and_Dam

Baldwin, C. (2026, April 6). Watershed | Fox Waterway Agency. Fox Waterway Agency. https://foxwaterway.com/watershed/

Black, E. M., Chimenti, M. S., & Just, C. L. (2017). Effect of freshwater mussels on the vertical distribution of anaerobic ammonia oxidizers and other nitrogen-transforming microorganisms in upper Mississippi river sediment. PeerJ, 5, e3536. https://doi.org/10.7717/peerj.3536

Carpentersville Dam Removal Project - Resource Environmental Solutions, LLC. (2025, February 18). Resource Environmental Solutions, LLC. https://res.us/projects/carpentersville-dam-removal-project/

Fox River. (2025). Chicagohistory.org. http://www.encyclopedia.chicagohistory.org/pages/481.html

Fox River Watershed | Lake County, IL. (2023). Lakecountyil.gov. https://www.lakecountyil.gov/2401/Fox-River-Watershed

Limpers, J. (2022, January 24). District’s Freshwater Mussels Help 3 Waterways. Dupageforest.org; FPDDC. https://www.dupageforest.org/blog/2021-mussel-releases

Merheb, M., Matar, R., Hodeify, R., Siddiqui, S. S., Vazhappilly, C. G., Marton, J., Azharuddin, S., & Al Zouabi, H. (2019). Mitochondrial DNA, a Powerful Tool to Decipher Ancient Human Civilization from Domestication to Music, and to Uncover Historical Murder Cases. Cells, 8(5), 433. https://doi.org/10.3390/cells8050433

Mohammed Abubakar, B., Mohd Salleh, F., Shamsir Omar, M. S., & Wagiran, A. (2017). Review: DNA Barcoding and Chromatography Fingerprints for the Authentication of Botanicals in Herbal Medicinal Products. Evidence-based complementary and alternative medicine : eCAM, 2017, 1352948. https://doi.org/10.1155/2017/1352948

Rock, S. L., Watz, J., Nilsson, P. A., & Österling, M. (2022). Effects of parasitic freshwater mussels on their host fishes: a review. Parasitology, 149(14), 1958–1975. https://doi.org/10.1017/S0031182022001226

Schanzle, R., Kruse, G., Kath, J., Klocek, R., & Cummings, K. (2004). The Freshwater Mussels Illinois and Wisconsin. https://ia801304.us.archive.org/28/items/freshwatermussel00scha/freshwatermussel00scha.pdf

Schilling, A. K., Mazzamuto, M. V., & Romeo, C. (2022). A Review of Non-Invasive Sampling in Wildlife Disease and Health Research: What's New?. Animals : an open access journal from MDPI, 12(13), 1719. https://doi.org/10.3390/ani12131719

Shasteen, D. K., Bales, S. A., & Stodola, A. P. (2013, March 19). Freshwater mussels of the Fox River basin in Illinois. Technical Report. https://www.ideals.illinois.edu/items/45966

Singh, A., Kumar, A., Kumar, R. S., Bhatt, D., & Gupta, S. K. (2017). Amplification of mtDNA control region in opportunistically collected bird samples belonging to nine families of the order Passeriformes. Mitochondrial DNA. Part B, Resources, 2(1), 99–100. https://doi.org/10.1080/23802359.2017.1289342

State of the Fox River Report 2003. (n.d.). https://prairierivers.org/wp-content/uploads/2007/09/stateoffoxriver2003-2.pdf

Yoon, H. J., Seo, J. H., Shin, S. H., Abdelhamid, M. A. A., & Pack, S. P. (2025). Bioinformation and Monitoring Technology for Environmental DNA Analysis: A Review. Biosensors, 15(8), 494. https://doi.org/10.3390/bios15080494

---