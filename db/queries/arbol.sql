-- DROP SCHEMA dbo;

CREATE SCHEMA dbo;
-- ArandanosProduccion.dbo.CUADRILLA definition
-- Drop table
-- DROP TABLE ArandanosProduccion.dbo.CUADRILLA;

CREATE TABLE ArandanosProduccion.dbo.CUADRILLA (
	id_Cuadrilla int IDENTITY(1, 1) NOT NULL,
	Clave varchar(20) COLLATE Modern_Spanish_CI_AS NOT NULL,
	Responsable varchar(200) COLLATE Modern_Spanish_CI_AS NOT NULL,
	Localidad varchar(100) COLLATE Modern_Spanish_CI_AS NULL,
	CONSTRAINT PK__CUADRILL__D967CD3B209D9612 PRIMARY KEY (id_Cuadrilla),
	CONSTRAINT UQ__CUADRILL__E8181E11084D27E5 UNIQUE (Clave)
);
-- ArandanosProduccion.dbo.FASE definition
-- Drop table
-- DROP TABLE ArandanosProduccion.dbo.FASE;

CREATE TABLE ArandanosProduccion.dbo.FASE (
	id_Fase int IDENTITY(1, 1) NOT NULL,
	Clave varchar(20) COLLATE Modern_Spanish_CI_AS NOT NULL,
	Ubicacion varchar(50) COLLATE Modern_Spanish_CI_AS NOT NULL,
	Nombre varchar(100) COLLATE Modern_Spanish_CI_AS NULL,
	CONSTRAINT PK__FASE__F5F964E911A575D1 PRIMARY KEY (id_Fase),
	CONSTRAINT UQ__FASE__E8181E1165F5B055 UNIQUE (Clave)
);
-- ArandanosProduccion.dbo.KEY_MODULOS definition
-- Drop table
-- DROP TABLE ArandanosProduccion.dbo.KEY_MODULOS;

CREATE TABLE ArandanosProduccion.dbo.KEY_MODULOS (
	id_Key int IDENTITY(1, 1) NOT NULL,
	Key_Modulos varchar(16) COLLATE Modern_Spanish_CI_AS NOT NULL,
	CONSTRAINT PK__KEY_MODU__6F7E19431715C648 PRIMARY KEY (id_Key)
);
-- ArandanosProduccion.dbo.MODALIDAD definition
-- Drop table
-- DROP TABLE ArandanosProduccion.dbo.MODALIDAD;

CREATE TABLE ArandanosProduccion.dbo.MODALIDAD (
	id_Modalidad int IDENTITY(1, 1) NOT NULL,
	Clave varchar(50) COLLATE Modern_Spanish_CI_AS NOT NULL,
	CONSTRAINT PK__MODALIDA__F93C3A8D9F95735F PRIMARY KEY (id_Modalidad),
	CONSTRAINT UQ__MODALIDA__E8181E11EDE8A439 UNIQUE (Clave)
);
-- ArandanosProduccion.dbo.USUARIO definition
-- Drop table
-- DROP TABLE ArandanosProduccion.dbo.USUARIO;

CREATE TABLE ArandanosProduccion.dbo.USUARIO (
	id_Usuario int IDENTITY(1, 1) NOT NULL,
	Nombre_Usuario varchar(50) COLLATE Modern_Spanish_CI_AS NOT NULL,
	Paswword_Acceso varchar(16) COLLATE Modern_Spanish_CI_AS NOT NULL,
	Rol varchar(50) COLLATE Modern_Spanish_CI_AS NOT NULL,
	Status bit NULL,
	CONSTRAINT PK__USUARIO__8E901EAA8F0754E8 PRIMARY KEY (id_Usuario)
);
-- ArandanosProduccion.dbo.sysdiagrams definition
-- Drop table
-- DROP TABLE ArandanosProduccion.dbo.sysdiagrams;

CREATE TABLE ArandanosProduccion.dbo.sysdiagrams (
	name sysname COLLATE Modern_Spanish_CI_AS NOT NULL,
	principal_id int NOT NULL,
	diagram_id int IDENTITY(1, 1) NOT NULL,
	version int NULL,
	definition varbinary(MAX) NULL,
	CONSTRAINT PK__sysdiagr__C2B05B616DFBCD08 PRIMARY KEY (diagram_id),
	CONSTRAINT UK_principal_name UNIQUE (principal_id,
name)
);
-- ArandanosProduccion.dbo.RECOLECTOR definition
-- Drop table
-- DROP TABLE ArandanosProduccion.dbo.RECOLECTOR;

CREATE TABLE ArandanosProduccion.dbo.RECOLECTOR (
	id_Recolector int IDENTITY(1, 1) NOT NULL,
	Nombre_Completo varchar(200) COLLATE Modern_Spanish_CI_AS NOT NULL,
	Encoder varbinary(MAX) NOT NULL,
	Foto_Recolector varbinary(MAX) NOT NULL,
	Localidad varchar(100) COLLATE Modern_Spanish_CI_AS NULL,
	Telefono varchar(50) COLLATE Modern_Spanish_CI_AS NULL,
	Fecha_Registro date NULL,
	Acceso bit NULL,
	id_Cuadrilla int NULL,
	CONSTRAINT PK__RECOLECT__3FA86BCDA680B215 PRIMARY KEY (id_Recolector),
	CONSTRAINT FK_RECOLECTOR_CUADRILLA FOREIGN KEY (id_Cuadrilla) REFERENCES ArandanosProduccion.dbo.CUADRILLA(id_Cuadrilla) ON
DELETE
    SET
    NULL
);
-- ArandanosProduccion.dbo.REGISTRO_CHECK definition
-- Drop table
-- DROP TABLE ArandanosProduccion.dbo.REGISTRO_CHECK;

CREATE TABLE ArandanosProduccion.dbo.REGISTRO_CHECK (
	id_Check int IDENTITY(1, 1) NOT NULL,
	Fecha_Hora_Check datetime NULL,
	id_Recolector int NULL,
	id_Modalidad int NULL,
	CONSTRAINT PK__REGISTRO__A3D32967DD83F738 PRIMARY KEY (id_Check),
	CONSTRAINT FK_CHECK_MODALIDAD FOREIGN KEY (id_Modalidad) REFERENCES ArandanosProduccion.dbo.MODALIDAD(id_Modalidad) ON
DELETE
    SET
    NULL,
    CONSTRAINT FK_CHECK_RECOLECTOR FOREIGN KEY (id_Recolector) REFERENCES ArandanosProduccion.dbo.RECOLECTOR(id_Recolector) ON
    DELETE
        SET
        NULL
);
-- ArandanosProduccion.dbo.TABLA definition
-- Drop table
-- DROP TABLE ArandanosProduccion.dbo.TABLA;

CREATE TABLE ArandanosProduccion.dbo.TABLA (
	id_Tabla int IDENTITY(1, 1) NOT NULL,
	Clave varchar(20) COLLATE Modern_Spanish_CI_AS NOT NULL,
	Ubicacion varchar(50) COLLATE Modern_Spanish_CI_AS NULL,
	Nombre varchar(100) COLLATE Modern_Spanish_CI_AS NULL,
	id_Fase int NULL,
	Clave_Trazabilidad varchar(128) COLLATE Modern_Spanish_CI_AS NULL,
	CONSTRAINT PK__TABLA__271C28288C290D0D PRIMARY KEY (id_Tabla),
	CONSTRAINT UQ__TABLA__E8181E117EB377F5 UNIQUE (Clave),
	CONSTRAINT FK_TABLA_FASE FOREIGN KEY (id_Fase) REFERENCES ArandanosProduccion.dbo.FASE(id_Fase) ON
DELETE
    SET
    NULL
);
-- ArandanosProduccion.dbo.MACROTUNEL definition
-- Drop table
-- DROP TABLE ArandanosProduccion.dbo.MACROTUNEL;

CREATE TABLE ArandanosProduccion.dbo.MACROTUNEL (
	id_Macrotunel int IDENTITY(1, 1) NOT NULL,
	Clave varchar(20) COLLATE Modern_Spanish_CI_AS NOT NULL,
	Ubicacion varchar(50) COLLATE Modern_Spanish_CI_AS NULL,
	Nombre varchar(100) COLLATE Modern_Spanish_CI_AS NULL,
	id_Tabla int NULL,
	Clave_Trazabilidad varchar(128) COLLATE Modern_Spanish_CI_AS NULL,
	CONSTRAINT PK__MACROTUN__A02C59BE4A9E967E PRIMARY KEY (id_Macrotunel),
	CONSTRAINT UQ__MACROTUN__E8181E116E1418A0 UNIQUE (Clave),
	CONSTRAINT FK_MACROTUNEL_TABLA FOREIGN KEY (id_Tabla) REFERENCES ArandanosProduccion.dbo.TABLA(id_Tabla) ON
DELETE
    SET
    NULL
);
-- ArandanosProduccion.dbo.LINEA definition
-- Drop table
-- DROP TABLE ArandanosProduccion.dbo.LINEA;

CREATE TABLE ArandanosProduccion.dbo.LINEA (
	id_Linea int IDENTITY(1, 1) NOT NULL,
	Clave varchar(20) COLLATE Modern_Spanish_CI_AS NOT NULL,
	Nombre varchar(100) COLLATE Modern_Spanish_CI_AS NULL,
	Ubicacion varchar(50) COLLATE Modern_Spanish_CI_AS NULL,
	Num_Macetas int NULL,
	id_Macrotunel int NULL,
	Clave_Trazabilidad varchar(128) COLLATE Modern_Spanish_CI_AS NULL,
	CONSTRAINT PK__LINEA__5584A0916F69F96B PRIMARY KEY (id_Linea),
	CONSTRAINT FK_LINEA_MACROTUNEL FOREIGN KEY (id_Macrotunel) REFERENCES ArandanosProduccion.dbo.MACROTUNEL(id_Macrotunel) ON
DELETE
    SET
    NULL
);
-- ArandanosProduccion.dbo.ENTREGA definition
-- Drop table
-- DROP TABLE ArandanosProduccion.dbo.ENTREGA;

CREATE TABLE ArandanosProduccion.dbo.ENTREGA (
	id_Entrega int IDENTITY(1, 1) NOT NULL,
	Clave varchar(20) COLLATE Modern_Spanish_CI_AS NOT NULL,
	Calificacion_Total varchar(20) COLLATE Modern_Spanish_CI_AS NULL,
	Peso_Total decimal(10, 3) NULL,
	Entrega_Inicio datetime DEFAULT getdate() NULL,
	Entrega_Final datetime DEFAULT getdate() NULL,
	id_Recolector int NULL,
	id_Linea int NULL,
	id_Modalidad int NULL,
	CONSTRAINT PK__ENTREGA__07C85F141792D7D8 PRIMARY KEY (id_Entrega),
	CONSTRAINT FK_ENTREGA_LINEA FOREIGN KEY (id_Linea) REFERENCES ArandanosProduccion.dbo.LINEA(id_Linea) ON
DELETE
    SET
    NULL,
    CONSTRAINT FK_ENTREGA_MODALIDAD FOREIGN KEY (id_Modalidad) REFERENCES ArandanosProduccion.dbo.MODALIDAD(id_Modalidad) ON
    DELETE
        SET
        NULL,
        CONSTRAINT FK_ENTREGA_RECOLECTOR FOREIGN KEY (id_Recolector) REFERENCES ArandanosProduccion.dbo.RECOLECTOR(id_Recolector) ON
        DELETE
            SET
            NULL
);
-- ArandanosProduccion.dbo.COSECHA definition
-- Drop table
-- DROP TABLE ArandanosProduccion.dbo.COSECHA;

CREATE TABLE ArandanosProduccion.dbo.COSECHA (
	id_Cosecha int IDENTITY(1, 1) NOT NULL,
	Clave varchar(20) COLLATE Modern_Spanish_CI_AS NOT NULL,
	Calificacion varchar(20) COLLATE Modern_Spanish_CI_AS NULL,
	Peso decimal(10, 3) NOT NULL,
	Foto_Cosecha varchar(64) COLLATE Modern_Spanish_CI_AS NULL,
	Fecha_Transaccion datetime DEFAULT getdate() NULL,
	id_Recolector int NULL,
	id_Linea int NULL,
	id_Entrega int NULL,
	id_Cuadrilla int NULL,
	id_Modalidad int NULL,
	Clave_Trazabilidad varchar(200) COLLATE Modern_Spanish_CI_AS NULL,
	CONSTRAINT PK__COSECHA__BD8697BF1212B8F3 PRIMARY KEY (id_Cosecha),
	CONSTRAINT FK_COSECHA_CUADRILLA FOREIGN KEY (id_Cuadrilla) REFERENCES ArandanosProduccion.dbo.CUADRILLA(id_Cuadrilla) ON
DELETE
    SET
    NULL,
    CONSTRAINT FK_COSECHA_ENTREGA FOREIGN KEY (id_Entrega) REFERENCES ArandanosProduccion.dbo.ENTREGA(id_Entrega) ON
    DELETE
        SET
        NULL,
        CONSTRAINT FK_COSECHA_LINEA FOREIGN KEY (id_Linea) REFERENCES ArandanosProduccion.dbo.LINEA(id_Linea) ON
        DELETE
            SET
            NULL,
            CONSTRAINT FK_COSECHA_MODALIDAD FOREIGN KEY (id_Modalidad) REFERENCES ArandanosProduccion.dbo.MODALIDAD(id_Modalidad) ON
            DELETE
                SET
                NULL,
                CONSTRAINT FK_COSECHA_RECOLECTOR FOREIGN KEY (id_Recolector) REFERENCES ArandanosProduccion.dbo.RECOLECTOR(id_Recolector) ON
                DELETE
                    SET
                    NULL
);
