-- # Class: FluxRecordTable Description: A list of flux records, e.g. one dataset flattened.
--     * Slot: id
-- # Class: FluxRecord Description: One flux value with the context needed to compare it across studies and tools. Multi-valued context (several experiments in a parallel labeling run) is joined with "; ".
--     * Slot: id
--     * Slot: dataset_id Description: FluxoDataset.id the row comes from.
--     * Slot: run_id Description: SimulationRun.id.
--     * Slot: reaction_id Description: Reaction (or atom-transition variant) id.
--     * Slot: flux_type Description: Net, forward, backward or exchange.
--     * Slot: value Description: Flux value.
--     * Slot: standard_deviation Description: Standard deviation of value.
--     * Slot: lower_ci Description: Lower bound of the uncertainty interval.
--     * Slot: upper_ci Description: Upper bound of the uncertainty interval.
--     * Slot: confidence_level Description: Level of lower_ci / upper_ci (e.g. 0.95).
--     * Slot: confidence_interval_method Description: How the interval was computed.
--     * Slot: flux_unit Description: Unit of value; compare rows only within one unit.
--     * Slot: solution_role Description: Estimated, reference (known truth) or simulated.
--     * Slot: fluxomics_method Description: Method of the run (FLUXO:0000021 subtree).
--     * Slot: run_mode Description: The run's modes, joined with "; ".
--     * Slot: software_name Description: Tool name; the free-text name when the enum value is "other".
--     * Slot: software_version Description: Tool version.
--     * Slot: investigation_id Description: Investigation the run belongs to.
--     * Slot: investigation_name Description: Its name.
--     * Slot: publication_doi Description: DOI of the investigation's publication.
--     * Slot: organism_name Description: Organism of the run's condition(s).
--     * Slot: strain Description: Strain of the run's condition(s).
--     * Slot: specific_growth_rate Description: Growth rate, when exactly one condition applies.
--     * Slot: growth_rate_unit Description: Unit of specific_growth_rate.
--     * Slot: data_origin Description: Experimental, synthetic or simulated (joined if mixed).
--     * Slot: stationary Description: Whether the run's experiments are isotopically stationary; empty when they disagree or the run has no experiment.
--     * Slot: tracer Description: Tracer design, e.g. "Gluc_ext: 100000 x 0.8, 111111 x 0.2", from LabelingExperiment.tracer_summary when given.
--     * Slot: wssr Description: The run's weighted sum of squared residuals.
--     * Slot: degrees_of_freedom Description: Degrees of freedom of the run's fit.
--     * Slot: chi_square_p_value Description: Upper-tail chi-square p-value of the run's fit.
--     * Slot: FluxRecordTable_id Description: Autocreated FK slot

CREATE TABLE "FluxRecordTable" (
	id INTEGER NOT NULL,
	PRIMARY KEY (id)
);
CREATE INDEX "ix_FluxRecordTable_id" ON "FluxRecordTable" (id);

CREATE TABLE "FluxRecord" (
	id INTEGER NOT NULL,
	dataset_id TEXT NOT NULL,
	run_id TEXT NOT NULL,
	reaction_id TEXT NOT NULL,
	flux_type VARCHAR(8) NOT NULL,
	value FLOAT NOT NULL,
	standard_deviation FLOAT,
	lower_ci FLOAT,
	upper_ci FLOAT,
	confidence_level FLOAT,
	confidence_interval_method VARCHAR(22),
	flux_unit TEXT,
	solution_role VARCHAR(9),
	fluxomics_method VARCHAR(22),
	run_mode TEXT,
	software_name TEXT,
	software_version TEXT,
	investigation_id TEXT,
	investigation_name TEXT,
	publication_doi TEXT,
	organism_name TEXT,
	strain TEXT,
	specific_growth_rate FLOAT,
	growth_rate_unit TEXT,
	data_origin TEXT,
	stationary BOOLEAN,
	tracer TEXT,
	wssr FLOAT,
	degrees_of_freedom INTEGER,
	chi_square_p_value FLOAT,
	"FluxRecordTable_id" INTEGER,
	PRIMARY KEY (id),
	FOREIGN KEY("FluxRecordTable_id") REFERENCES "FluxRecordTable" (id)
);
CREATE INDEX "ix_FluxRecord_id" ON "FluxRecord" (id);
