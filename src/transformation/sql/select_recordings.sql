WITH
clean_recordings AS (
	SELECT
		*
	FROM recordings r
	WHERE r.status = 'identified'
	  AND r.file IS NOT NULL
	  AND r.method IS NOT NULL
	  AND r.method != 'in the hand'
	  AND r.type IS NOT NULL
	  AND (
	        r.type LIKE '%song%'
	        OR r.type LIKE '%canto%'
	        OR r.type LIKE '%call%'
	        OR r.type LIKE '%chamado%'
	      )
	  AND (r.smp IS NULL OR r.smp >= 22050)
	  AND r.length_s >= 3
),
forest_join AS (
	SELECT
		cr.*,
		inf.in_atlantic_forest
	FROM clean_recordings cr
	LEFT JOIN gold.in_forest inf
	ON cr.id = inf.id
),
cirterios_especies AS (
	SELECT
		iaf.species,
		SUM(CASE WHEN iaf.in_atlantic_forest = 1 THEN 1 ELSE 0 END) as grav_dentro,
		COUNT(DISTINCT iaf.rec) as aut_brasil
	FROM forest_join iaf
	GROUP BY iaf.species
),
especies_selecionadas AS (
	SELECT
		ce.species
	FROM cirterios_especies ce
	WHERE ce.grav_dentro >= :min_grav_dentro
	AND ce.aut_brasil >= :min_aut_brasil
),
gravacoes_contaminadas AS (
	SELECT
		DISTINCT fj.id
	FROM forest_join fj
	INNER JOIN background_species bs
	ON fj.id = bs.recording_id
	WHERE fj.species IN (SELECT species FROM especies_selecionadas)
	AND bs.species IN (SELECT species FROM especies_selecionadas)
	AND fj.species != bs.species
)
SELECT
	fj.id,
	fj.species,
	fj.rec,
	fj.file,
	fj.lic,
	fj.length_s,
	fj.smp,
	fj.in_atlantic_forest
FROM forest_join fj
WHERE fj.id NOT IN (SELECT id FROM gravacoes_contaminadas)
AND fj.species IN (SELECT species FROM especies_selecionadas)



