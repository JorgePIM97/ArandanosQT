-- Crear la base de datos (si no existe)
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'ArandanosTest')
BEGIN
    CREATE DATABASE ArandanosTest;
END
GO

USE ArandanosTest;
GO

-- Tabla CUADRILLA
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'CUADRILLA')
BEGIN
    CREATE TABLE CUADRILLA (
        id_Cuadrilla INT IDENTITY(1,1) PRIMARY KEY,
        Clave NVARCHAR(20) NOT NULL,
        Responsable NVARCHAR(200),
        Localidad NVARCHAR(100)
    );
    PRINT 'Tabla CUADRILLA creada exitosamente';
END
ELSE
    PRINT 'La tabla CUADRILLA ya existe';
GO

-- Tabla RECOLECTOR
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'RECOLECTOR')
BEGIN
    CREATE TABLE RECOLECTOR (
        id_Recolector INT IDENTITY(1,1) PRIMARY KEY,
        Nombre_Completo NVARCHAR(200) NOT NULL,
        Encoder VARBINARY(MAX),
        Foto_Recolector VARBINARY(MAX),
        Localidad NVARCHAR(100),
        Telefono NVARCHAR(50),
        Fecha_Registro DATETIME DEFAULT GETDATE(),
        Acceso BIT,
        id_Cuadrilla INT,
        CONSTRAINT FK_Recolector_Cuadrilla FOREIGN KEY (id_Cuadrilla) 
            REFERENCES CUADRILLA(id_Cuadrilla) ON DELETE SET NULL
    );
    PRINT 'Tabla RECOLECTOR creada exitosamente';
END
ELSE
    PRINT 'La tabla RECOLECTOR ya existe';
GO

-- Tabla TABLA
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'TABLA')
BEGIN
    CREATE TABLE TABLA (
        id_Tabla INT IDENTITY(1,1) PRIMARY KEY,
        Clave NVARCHAR(20) NOT NULL,
        Ubicacion NVARCHAR(50),
        Descripcion NVARCHAR(50),
        Num_Macrotuneles INT
    );
    PRINT 'Tabla TABLA creada exitosamente';
END
ELSE
    PRINT 'La tabla TABLA ya existe';
GO

-- Tabla MACROTUNEL
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'MACROTUNEL')
BEGIN
    CREATE TABLE MACROTUNEL (
        id_Macrotunel INT IDENTITY(1,1) PRIMARY KEY,
        Clave NVARCHAR(20) NOT NULL,
        Descripcion NVARCHAR(50),
        Num_Pasillos INT,
        id_Tabla INT,
        CONSTRAINT FK_Macrotunel_Tabla FOREIGN KEY (id_Tabla) 
            REFERENCES TABLA(id_Tabla) ON DELETE SET NULL
    );
    PRINT 'Tabla MACROTUNEL creada exitosamente';
END
ELSE
    PRINT 'La tabla MACROTUNEL ya existe';
GO

-- Tabla ENTREGA
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ENTREGA')
BEGIN
    CREATE TABLE ENTREGA (
        id_Entrega INT IDENTITY(1,1) PRIMARY KEY,
        Clave NVARCHAR(20) NOT NULL,
        Calificacion_Total NVARCHAR(20),
        Peso_Total FLOAT,
        Entrega_Inicio DATETIME DEFAULT GETDATE(),
        Entrega_Final DATETIME,
        id_Recolector INT,
        id_Macrotunel INT,
        CONSTRAINT FK_Entrega_Recolector FOREIGN KEY (id_Recolector) 
            REFERENCES RECOLECTOR(id_Recolector) ON DELETE SET NULL,
        CONSTRAINT FK_Entrega_Macrotunel FOREIGN KEY (id_Macrotunel) 
            REFERENCES MACROTUNEL(id_Macrotunel) ON DELETE SET NULL
    );
    PRINT 'Tabla ENTREGA creada exitosamente';
END
ELSE
    PRINT 'La tabla ENTREGA ya existe';
GO

-- Tabla COSECHA
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'COSECHA')
BEGIN
    CREATE TABLE COSECHA (
        id_Cosecha INT IDENTITY(1,1) PRIMARY KEY,
        Clave NVARCHAR(20) NOT NULL,
        Calificacion NVARCHAR(20),
        Peso FLOAT,
        Foto_Cosecha NVARCHAR(200),
        Fecha_Transaccion DATETIME DEFAULT GETDATE(),
        id_Recolector INT,
        id_Macrotunel INT,
        id_Entrega INT,
        CONSTRAINT FK_Cosecha_Recolector FOREIGN KEY (id_Recolector) 
            REFERENCES RECOLECTOR(id_Recolector) ON DELETE SET NULL,
        CONSTRAINT FK_Cosecha_Macrotunel FOREIGN KEY (id_Macrotunel) 
            REFERENCES MACROTUNEL(id_Macrotunel) ON DELETE SET NULL,
        CONSTRAINT FK_Cosecha_Entrega FOREIGN KEY (id_Entrega) 
            REFERENCES ENTREGA(id_Entrega) ON DELETE SET NULL
    );
    PRINT 'Tabla COSECHA creada exitosamente';
END
ELSE
    PRINT 'La tabla COSECHA ya existe';
GO

-- Crear �ndices para mejorar el rendimiento
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_RECOLLECTOR_NOMBRE')
    CREATE INDEX IX_RECOLLECTOR_NOMBRE ON RECOLECTOR(Nombre_Completo);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_COSECHA_FECHA')
    CREATE INDEX IX_COSECHA_FECHA ON COSECHA(Fecha_Transaccion);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_ENTREGA_FECHA')
    CREATE INDEX IX_ENTREGA_FECHA ON ENTREGA(Entrega_Inicio);
GO

PRINT 'Esquema de base de datos creado exitosamente';
GO