CREATE OR ALTER TRIGGER trg_TABLA_Trazabilidad
ON dbo.TABLA
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    -- Evitar recursión si el UPDATE es solo de Clave_Trazabilidad
    IF UPDATE(Clave_Trazabilidad) AND NOT UPDATE(Clave) AND NOT UPDATE(id_Fase)
        RETURN;

    UPDATE t
    SET t.Clave_Trazabilidad = 
        CASE 
            WHEN f.Clave IS NOT NULL 
                THEN f.Clave + '-' + t.Clave   -- Ej: "F1-T2"
            ELSE t.Clave                         -- Sin FASE asignada
        END
    FROM dbo.TABLA t
    INNER JOIN inserted i ON t.id_Tabla = i.id_Tabla
    LEFT JOIN dbo.FASE f ON t.id_Fase = f.id_Fase;
END
GO


CREATE OR ALTER TRIGGER trg_MACROTUNEL_Trazabilidad
ON dbo.MACROTUNEL
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    IF UPDATE(Clave_Trazabilidad) AND NOT UPDATE(Clave) AND NOT UPDATE(id_Tabla)
        RETURN;

    UPDATE mt
    SET mt.Clave_Trazabilidad = 
        CASE 
            WHEN tb.Clave_Trazabilidad IS NOT NULL 
                THEN tb.Clave_Trazabilidad + '-' + mt.Clave  -- Ej: "F1-T2-MT5"
            ELSE mt.Clave
        END
    FROM dbo.MACROTUNEL mt
    INNER JOIN inserted i ON mt.id_Macrotunel = i.id_Macrotunel
    LEFT JOIN dbo.TABLA tb ON mt.id_Tabla = tb.id_Tabla;
END
GO


CREATE OR ALTER TRIGGER trg_LINEA_Trazabilidad
ON dbo.LINEA
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    IF UPDATE(Clave_Trazabilidad) AND NOT UPDATE(Clave) AND NOT UPDATE(id_Macrotunel)
        RETURN;

    UPDATE l
    SET l.Clave_Trazabilidad = 
        CASE 
            WHEN mt.Clave_Trazabilidad IS NOT NULL 
                THEN mt.Clave_Trazabilidad + '-' + l.Clave  -- Ej: "F1-T2-MT5-L1"
            ELSE l.Clave
        END
    FROM dbo.LINEA l
    INNER JOIN inserted i ON l.id_Linea = i.id_Linea
    LEFT JOIN dbo.MACROTUNEL mt ON l.id_Macrotunel = mt.id_Macrotunel;
END
GO


--Trigger en FASE — Propaga a TABLA → MACROTUNEL → LINEA
CREATE OR ALTER TRIGGER trg_FASE_Propagar_Trazabilidad
ON dbo.FASE
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    -- Solo actuar si cambió la Clave
    IF NOT UPDATE(Clave)
        RETURN;

    -- 1. Actualizar TABLA hijos directos
    UPDATE t
    SET t.Clave_Trazabilidad =
        CASE
            WHEN f.Clave IS NOT NULL THEN f.Clave + '-' + t.Clave
            ELSE t.Clave
        END
    FROM dbo.TABLA t
    INNER JOIN inserted f ON t.id_Fase = f.id_Fase;

    -- 2. Actualizar MACROTUNEL (nietos) a partir de las TABLA ya actualizadas
    UPDATE mt
    SET mt.Clave_Trazabilidad =
        CASE
            WHEN tb.Clave_Trazabilidad IS NOT NULL THEN tb.Clave_Trazabilidad + '-' + mt.Clave
            ELSE mt.Clave
        END
    FROM dbo.MACROTUNEL mt
    INNER JOIN dbo.TABLA tb ON mt.id_Tabla = tb.id_Tabla
    INNER JOIN inserted f ON tb.id_Fase = f.id_Fase;

    -- 3. Actualizar LINEA (bisnietos) a partir de los MACROTUNEL ya actualizados
    UPDATE l
    SET l.Clave_Trazabilidad =
        CASE
            WHEN mt.Clave_Trazabilidad IS NOT NULL THEN mt.Clave_Trazabilidad + '-' + l.Clave
            ELSE l.Clave
        END
    FROM dbo.LINEA l
    INNER JOIN dbo.MACROTUNEL mt ON l.id_Macrotunel = mt.id_Macrotunel
    INNER JOIN dbo.TABLA tb ON mt.id_Tabla = tb.id_Tabla
    INNER JOIN inserted f ON tb.id_Fase = f.id_Fase;

END
GO

--Trigger en TABLA — Propaga a MACROTUNEL → LINEA
CREATE OR ALTER TRIGGER trg_TABLA_Propagar_Trazabilidad
ON dbo.TABLA
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    -- Solo actuar si cambió la Clave o la Clave_Trazabilidad (por propagación desde FASE)
    IF NOT UPDATE(Clave) AND NOT UPDATE(Clave_Trazabilidad)
        RETURN;

    -- 1. Actualizar MACROTUNEL hijos directos
    UPDATE mt
    SET mt.Clave_Trazabilidad =
        CASE
            WHEN tb.Clave_Trazabilidad IS NOT NULL THEN tb.Clave_Trazabilidad + '-' + mt.Clave
            ELSE mt.Clave
        END
    FROM dbo.MACROTUNEL mt
    INNER JOIN inserted tb ON mt.id_Tabla = tb.id_Tabla;

    -- 2. Actualizar LINEA (nietos) a partir de los MACROTUNEL ya actualizados
    UPDATE l
    SET l.Clave_Trazabilidad =
        CASE
            WHEN mt.Clave_Trazabilidad IS NOT NULL THEN mt.Clave_Trazabilidad + '-' + l.Clave
            ELSE l.Clave
        END
    FROM dbo.LINEA l
    INNER JOIN dbo.MACROTUNEL mt ON l.id_Macrotunel = mt.id_Macrotunel
    INNER JOIN inserted tb ON mt.id_Tabla = tb.id_Tabla;

END
GO

--Trigger en MACROTUNEL — Propaga a LINEA
CREATE OR ALTER TRIGGER trg_MACROTUNEL_Propagar_Trazabilidad
ON dbo.MACROTUNEL
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    -- Solo actuar si cambió la Clave o la Clave_Trazabilidad (por propagación desde TABLA)
    IF NOT UPDATE(Clave) AND NOT UPDATE(Clave_Trazabilidad)
        RETURN;

    -- Actualizar LINEA hijos directos
    UPDATE l
    SET l.Clave_Trazabilidad =
        CASE
            WHEN mt.Clave_Trazabilidad IS NOT NULL THEN mt.Clave_Trazabilidad + '-' + l.Clave
            ELSE l.Clave
        END
    FROM dbo.LINEA l
    INNER JOIN inserted mt ON l.id_Macrotunel = mt.id_Macrotunel;

END
GO