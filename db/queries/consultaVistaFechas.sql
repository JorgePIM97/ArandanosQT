DECLARE @fecha1 as datetime
DECLARE @fecha2 as datetime
SET @fecha1 = '2025-05-01'
SET @fecha2 = '2025-05-01'
select * from vw_Cosecha v
WHERE v.[Fecha_Transaccion] between @fecha1 and @fecha2


DECLARE @fecha1 as datetime
SET @fecha1 = '2025-05-01'
SELECT * FROM vw_Cosecha v
WHERE CAST(v.[Fecha_Transaccion] AS DATE) = @fecha1


DECLARE @fecha1 as datetime
DECLARE @fecha2 as datetime
SET @fecha1 = '2025-05-01'
SET @fecha2 = '2025-06-02'
SELECT * FROM vw_Cosecha v
WHERE v.[Fecha_Transaccion] >= @fecha1 
AND v.[Fecha_Transaccion] < DATEADD(day, 1, @fecha2)  -- Hasta 2025-06-03 00:00:00 (excluido)


DECLARE @nombre as VARCHAR(200)
SET @nombre = 'ALONSO'
SELECT * FROM vw_CosechaVista v
WHERE CAST(v.[NOMBRE COMPLETO] AS VARCHAR) = @nombre


DECLARE @macrotunel as VARCHAR(20)
SET @macrotunel = 'MT05'
SELECT * FROM vw_CosechaVista v
WHERE CAST(v.[MACROTUNEL] AS VARCHAR) = @macrotunel

DECLARE @tabla as VARCHAR(20)
SET @tabla = 'T07'
SELECT * FROM vw_CosechaVista v
WHERE CAST(v.[TABLA] AS VARCHAR) = @tabla


DECLARE @nombreRecolector as VARCHAR(200)
SET @nombreRecolector = 'ALONSO GUZMAN'
  SELECT 
    CONVERT(DATE, e.Entrega_Inicio) AS Fecha,
    r.Nombre_Completo AS Nombre,
	COUNT(e.id_Entrega) AS [Total Entregas],
	SUM(e.Peso_Total) AS [Peso Total Acumulado],
    SUM(CASE WHEN e.Calificacion_Total = 'Buena' THEN 1 ELSE 0 END) AS [Total Buenas],
    SUM(CASE WHEN e.Calificacion_Total = 'Regular' THEN 1 ELSE 0 END) AS [Total Regulares],
    SUM(CASE WHEN e.Calificacion_Total = 'Mala' THEN 1 ELSE 0 END) AS [Total Malas]    
FROM 
    ENTREGA e
INNER JOIN 
    RECOLECTOR r ON e.id_Recolector = r.id_Recolector
WHERE 
    r.Nombre_Completo LIKE '%' + @nombreRecolector + '%'
    AND CONVERT(DATE, e.Entrega_Inicio) = CONVERT(DATE, GETDATE())
GROUP BY 
    CONVERT(DATE, e.Entrega_Inicio),
    r.Nombre_Completo
ORDER BY 
    Fecha, Nombre;



SELECT 
    r.Nombre_Completo AS Nombre,
    COUNT(e.id_Entrega) AS [T. Entregas],
    SUM(e.Peso_Total) AS [Peso Total],
    SUM(CASE WHEN e.Calificacion_Total = 'Buena' THEN 1 ELSE 0 END) AS [T. Buenas],
    SUM(CASE WHEN e.Calificacion_Total = 'Regular' THEN 1 ELSE 0 END) AS [T. Regulares],
    SUM(CASE WHEN e.Calificacion_Total = 'Mala' THEN 1 ELSE 0 END) AS [T. Malas]
FROM 
    ENTREGA e
INNER JOIN 
    RECOLECTOR r ON e.id_Recolector = r.id_Recolector
WHERE 
    CAST(e.Entrega_Inicio AS DATE) = CAST(GETDATE() AS DATE)
GROUP BY 
    r.Nombre_Completo
ORDER BY 
    [Peso Total] DESC;