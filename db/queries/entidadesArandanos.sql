-- Crear la base de datos si no existe
CREATE DATABASE ArandanosDB;
GO

-- Usar la base de datos
USE ArandanosDB;
GO

-- Tabla CUADRILLA
CREATE TABLE CUADRILLA (
    id_Cuadrilla INT IDENTITY(1,1) PRIMARY KEY,
    Clave VARCHAR(20) NOT NULL,
    Responsable VARCHAR(200),
    Localidad VARCHAR(100)
);

-- Tabla RECOLECTOR
CREATE TABLE RECOLECTOR (
    id_Recolector INT IDENTITY(1,1) PRIMARY KEY,
    Nombre_Completo VARCHAR(200) NOT NULL,
    Encoder VARBINARY(MAX) NOT NULL,
    Foto_Recolector VARBINARY(MAX) NOT NULL,
    Localidad VARCHAR(100),
    Telefono VARCHAR(50),
    Fecha_Registro DATE,
    Acceso BIT,  -- BOOL no existe en SQL Server, se usa BIT
    id_Cuadrilla INT FOREIGN KEY REFERENCES CUADRILLA(id_Cuadrilla) ON DELETE SET NULL
);

-- Tabla COSECHA
CREATE TABLE COSECHA (
    id_Cosecha INT IDENTITY(1,1) PRIMARY KEY,
    Clave VARCHAR(20) NOT NULL,
    Calificacion VARCHAR(20),
    Peso FLOAT,  -- double no es un tipo de dato en SQL Server, se usa FLOAT o DECIMAL
    Foto_Cosecha VARBINARY(MAX) NOT NULL,
    Fecha_Transaccion DATETIME DEFAULT GETDATE(),
    id_Recolector INT FOREIGN KEY REFERENCES RECOLECTOR(id_Recolector) ON DELETE SET NULL,
    id_Macrotunel INT FOREIGN KEY REFERENCES MACROTUNEL(id_Macrotunel) ON DELETE SET NULL
);

-- Tabla MACROTUNEL
CREATE TABLE MACROTUNEL (
    id_Macrotunel INT IDENTITY(1,1) PRIMARY KEY,
    Clave VARCHAR(20) NOT NULL,
    Descripcion VARCHAR(50),
    Num_Pasillos INT,
    id_Tabla INT FOREIGN KEY REFERENCES TABLA(id_Tabla) ON DELETE SET NULL
);

-- Tabla TABLA
CREATE TABLE TABLA (
    id_Tabla INT IDENTITY(1,1) PRIMARY KEY,
    Clave VARCHAR(20) NOT NULL,
    Ubicacion VARCHAR(50),
    Descripcion VARCHAR(50),
    Num_Macrotuneles INT
);

-- Tabla ENTREGA
CREATE TABLE ENTREGA (
    id_Entrega INT IDENTITY(1,1) PRIMARY KEY,
    Clave VARCHAR(20) NOT NULL,
    Calificacion_Total VARCHAR(20),
    Peso_Total FLOAT,  
    Entrega_Inicio DATETIME DEFAULT GETDATE(),
	Entrega_Final DATETIME DEFAULT GETDATE(),
    id_Recolector INT FOREIGN KEY REFERENCES RECOLECTOR(id_Recolector) ON DELETE SET NULL,
    id_Macrotunel INT FOREIGN KEY REFERENCES MACROTUNEL(id_Macrotunel) ON DELETE SET NULL
);

select * from COSECHA
select * from CUADRILLA
select * from RECOLECTOR


ALTER TABLE COSECHA
ADD id_Entrega INT NULL,
CONSTRAINT FK_Cosecha_Entrega FOREIGN KEY (id_Entrega) REFERENCES ENTREGA(id_Entrega) ON DELETE SET NULL;