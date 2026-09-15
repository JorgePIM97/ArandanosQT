-- ============================================================
--  Base de Datos: ArandanosProduccion
--  Descripcion  : Script de creacion de base de datos y tablas
--  Notas        : - Se corrigio referencia circular entre
--                   COSECHA y ENTREGA (id_Entrega se agrega
--                   como ALTER TABLE despues de crear ENTREGA).
--                 - CHECK es palabra reservada en SQL Server;
--                   la tabla se renombro a REGISTRO_CHECK.
--                 - Se usa DECIMAL(10,3) en lugar de FLOAT
--                   para pesos (mayor precision).
-- ============================================================

-- ------------------------------------------------------------
-- 1. Crear la base de datos si no existe
-- ------------------------------------------------------------
IF NOT EXISTS (
    SELECT name FROM sys.databases WHERE name = 'ArandanosProduccion'
)
BEGIN
    CREATE DATABASE ArandanosProduccion;
END
GO

USE ArandanosProduccion;
GO

-- ------------------------------------------------------------
-- 2. Tabla FASE
-- ------------------------------------------------------------
IF OBJECT_ID('dbo.FASE', 'U') IS NULL
BEGIN
    CREATE TABLE FASE (
        id_Fase     INT          IDENTITY(1,1) PRIMARY KEY,
        Clave       VARCHAR(20)  UNIQUE NOT NULL,
        Ubicacion   VARCHAR(50)  NOT NULL,
        Nombre VARCHAR(100) NULL
        
    );
END
GO

-- ------------------------------------------------------------
-- 3. Tabla TABLA
-- ------------------------------------------------------------
IF OBJECT_ID('dbo.TABLA', 'U') IS NULL
BEGIN
    CREATE TABLE TABLA (
        id_Tabla         INT         IDENTITY(1,1) PRIMARY KEY,
        Clave            VARCHAR(20) UNIQUE NOT NULL,
        Ubicacion        VARCHAR(50) NULL,
        Nombre           VARCHAR(100) NULL,
        id_Fase          INT         NULL,
        Clave_Trazabilidad VARCHAR(128) NULL,
        CONSTRAINT FK_TABLA_FASE
            FOREIGN KEY (id_Fase) REFERENCES FASE(id_Fase) ON DELETE SET NULL
    );
END
GO

-- ------------------------------------------------------------
-- 4. Tabla MACROTUNEL
-- ------------------------------------------------------------
IF OBJECT_ID('dbo.MACROTUNEL', 'U') IS NULL
BEGIN
    CREATE TABLE MACROTUNEL (
        id_Macrotunel INT         IDENTITY(1,1) PRIMARY KEY,
        Clave         VARCHAR(20) UNIQUE NOT NULL,
        Ubicacion     VARCHAR(50) NULL,
        Nombre        VARCHAR(100) NULL,
        id_Tabla      INT         NULL,
        Clave_Trazabilidad VARCHAR(128) NULL,
        CONSTRAINT FK_MACROTUNEL_TABLA
            FOREIGN KEY (id_Tabla) REFERENCES TABLA(id_Tabla) ON DELETE SET NULL
    );
END
GO

-- ------------------------------------------------------------
-- 5. Tabla LINEA
-- ------------------------------------------------------------
IF OBJECT_ID('dbo.LINEA', 'U') IS NULL
BEGIN
    CREATE TABLE LINEA (
        id_Linea      INT         IDENTITY(1,1) PRIMARY KEY,
        Clave         VARCHAR(20) NOT NULL,
        Nombre        VARCHAR(100) NULL,
        Ubicacion     VARCHAR(50) NULL,
        Num_Macetas   INT         NULL,
        id_Macrotunel INT         NULL,
        Clave_Trazabilidad VARCHAR(128) NULL,
        CONSTRAINT FK_LINEA_MACROTUNEL
            FOREIGN KEY (id_Macrotunel) REFERENCES MACROTUNEL(id_Macrotunel) ON DELETE SET NULL
    );
END
GO

-- ------------------------------------------------------------
-- 6. Tabla MODALIDAD
-- ------------------------------------------------------------
IF OBJECT_ID('dbo.MODALIDAD', 'U') IS NULL
BEGIN
    CREATE TABLE MODALIDAD (
        id_Modalidad INT         IDENTITY(1,1) PRIMARY KEY,
        Clave        VARCHAR(50) UNIQUE NOT NULL
    );
END
GO

-- ------------------------------------------------------------
-- 7. Tabla CUADRILLA
-- ------------------------------------------------------------
IF OBJECT_ID('dbo.CUADRILLA', 'U') IS NULL
BEGIN
    CREATE TABLE CUADRILLA (
        id_Cuadrilla INT          IDENTITY(1,1) PRIMARY KEY,
        Clave        VARCHAR(20)  UNIQUE NOT NULL,
        Responsable  VARCHAR(200) NOT NULL,
        Localidad    VARCHAR(100) NULL
    );
END
GO

-- ------------------------------------------------------------
-- 8. Tabla RECOLECTOR
-- ------------------------------------------------------------
IF OBJECT_ID('dbo.RECOLECTOR', 'U') IS NULL
BEGIN
    CREATE TABLE RECOLECTOR (
        id_Recolector   INT            IDENTITY(1,1) PRIMARY KEY,
        Nombre_Completo VARCHAR(200)   NOT NULL,
        Encoder         VARBINARY(MAX) NOT NULL,
        Foto_Recolector VARBINARY(MAX) NOT NULL,
        Localidad       VARCHAR(100)   NULL,
        Telefono        VARCHAR(50)    NULL,
        Fecha_Registro  DATE           NULL,
        Acceso          BIT            NULL,
        id_Cuadrilla    INT            NULL,
        CONSTRAINT FK_RECOLECTOR_CUADRILLA
            FOREIGN KEY (id_Cuadrilla) REFERENCES CUADRILLA(id_Cuadrilla) ON DELETE SET NULL
    );
END
GO

-- ------------------------------------------------------------
-- 9. Tabla ENTREGA
--    (Se crea ANTES de COSECHA para evitar referencia circular)
-- ------------------------------------------------------------
IF OBJECT_ID('dbo.ENTREGA', 'U') IS NULL
BEGIN
    CREATE TABLE ENTREGA (
        id_Entrega         INT           IDENTITY(1,1) PRIMARY KEY,
        Clave              VARCHAR(20)   NOT NULL,
        Calificacion_Total VARCHAR(20)   NULL,
        Peso_Total         DECIMAL(10,3) NULL,
        Entrega_Inicio     DATETIME      DEFAULT GETDATE(),
        Entrega_Final      DATETIME      DEFAULT GETDATE(),
        id_Recolector      INT           NULL,
        id_Linea           INT           NULL,
        id_Modalidad       INT           NULL,
        CONSTRAINT FK_ENTREGA_RECOLECTOR
            FOREIGN KEY (id_Recolector) REFERENCES RECOLECTOR(id_Recolector) ON DELETE SET NULL,
        CONSTRAINT FK_ENTREGA_LINEA
            FOREIGN KEY (id_Linea)      REFERENCES LINEA(id_Linea)           ON DELETE SET NULL,
        CONSTRAINT FK_ENTREGA_MODALIDAD
            FOREIGN KEY (id_Modalidad)  REFERENCES MODALIDAD(id_Modalidad)   ON DELETE SET NULL
    );
END
GO

-- ------------------------------------------------------------
-- 10. Tabla COSECHA
--     (Referencia a ENTREGA resuelta: ENTREGA ya existe)
-- ------------------------------------------------------------
IF OBJECT_ID('dbo.COSECHA', 'U') IS NULL
BEGIN
    CREATE TABLE COSECHA (
        id_Cosecha        INT           IDENTITY(1,1) PRIMARY KEY,
        Clave             VARCHAR(20)   NOT NULL,
        Calificacion      VARCHAR(20)   NULL,
        Peso              DECIMAL(10,3) NOT NULL,
        Foto_Cosecha      VARCHAR(64)   NULL,
        Fecha_Transaccion DATETIME      DEFAULT GETDATE(),
        id_Recolector     INT           NULL,
        id_Linea          INT           NULL,
        id_Entrega        INT           NULL,
        id_Cuadrilla      INT           NULL,
        id_Modalidad      INT           NULL,
        Clave_Trazabilidad VARCHAR(128) NULL,
        CONSTRAINT FK_COSECHA_RECOLECTOR
            FOREIGN KEY (id_Recolector) REFERENCES RECOLECTOR(id_Recolector) ON DELETE SET NULL,
        CONSTRAINT FK_COSECHA_LINEA
            FOREIGN KEY (id_Linea)      REFERENCES LINEA(id_Linea)           ON DELETE SET NULL,
        CONSTRAINT FK_COSECHA_ENTREGA
            FOREIGN KEY (id_Entrega)    REFERENCES ENTREGA(id_Entrega)       ON DELETE SET NULL,
        CONSTRAINT FK_COSECHA_CUADRILLA
            FOREIGN KEY (id_Cuadrilla)  REFERENCES CUADRILLA(id_Cuadrilla)   ON DELETE SET NULL,
        CONSTRAINT FK_COSECHA_MODALIDAD
            FOREIGN KEY (id_Modalidad)  REFERENCES MODALIDAD(id_Modalidad)   ON DELETE SET NULL
    );
END
GO

-- ------------------------------------------------------------
-- 11. Tabla REGISTRO_CHECK
--     (Renombrada: CHECK es palabra reservada en SQL Server)
-- ------------------------------------------------------------
IF OBJECT_ID('dbo.REGISTRO_CHECK', 'U') IS NULL
BEGIN
    CREATE TABLE REGISTRO_CHECK (
        id_Check         INT      IDENTITY(1,1) PRIMARY KEY,
        Fecha_Hora_Check DATETIME NULL,
        id_Recolector    INT      NULL,
        id_Modalidad     INT      NULL,
        CONSTRAINT FK_CHECK_RECOLECTOR
            FOREIGN KEY (id_Recolector) REFERENCES RECOLECTOR(id_Recolector) ON DELETE SET NULL,
        CONSTRAINT FK_CHECK_MODALIDAD
            FOREIGN KEY (id_Modalidad)  REFERENCES MODALIDAD(id_Modalidad)   ON DELETE SET NULL
    );
END
GO

IF OBJECT_ID('dbo.KEY_MODULOS', 'U') IS NULL
BEGIN
    CREATE TABLE KEY_MODULOS (
id_Key INT IDENTITY(1,1) PRIMARY KEY,
Key_Modulos VARCHAR(16)  NOT NULL
    );
END
GO

IF OBJECT_ID('dbo.USUARIO', 'U') IS NULL
BEGIN
    CREATE TABLE USUARIO (
id_Usuario  INT IDENTITY(1,1) PRIMARY KEY,
Nombre_Usuario VARCHAR(50)  NOT NULL,
Paswword_Acceso  VARCHAR(16)  NOT NULL,
Rol  VARCHAR(50) NOT NULL, 
Status BIT
    );
END
GO

INSER INTO dbo.KEY_MODULOS VALUES ('1234')

INSERT INTO dbo.USUARIO values ('ADMIN1', '1234', 'ADMIN', 1)

-- ------------------------------------------------------------
-- Fin del script
-- ------------------------------------------------------------
PRINT 'Base de datos ArandanosProduccion creada correctamente.';
GO