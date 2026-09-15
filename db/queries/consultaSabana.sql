--sabana de datos primera version
create view vw_Cosecha AS
SELECT [id_Cosecha]
      ,c.[Clave]
      ,[Calificacion]
      ,[Peso]
      ,[Foto_Cosecha]
      ,[Fecha_Transaccion]
      ,c.[id_Recolector]
	  ,r.Nombre_Completo
      ,m.[id_Macrotunel]
	  ,m.id_Tabla
	  ,m.Clave 'clave macrotunel'
      ,[id_Entrega],
	  t.Clave 'TABLA'
  FROM [ArandanosDB].[dbo].[COSECHA] c
  inner join RECOLECTOR r on r.id_Recolector = c.id_Recolector
  inner join MACROTUNEL m on m.id_Macrotunel = c.id_Macrotunel
  inner join TABLA t on m.id_Tabla = t.id_Tabla

--sabana de datos segunda version
create view vw_CosechaVista AS
SELECT [id_Cosecha] 'ID COSECHA'
      ,c.[Clave] 'CLAVE'
      ,[Calificacion] 'CALIFICACION'
      ,[Peso] 'PESO'
      ,[Fecha_Transaccion] 'FECHA TRANSACCION'
      ,c.[id_Recolector] 'ID RECOLECTOR'
	  ,r.Nombre_Completo 'NOMBRE COMPLETO'
      --,m.[id_Macrotunel]
	  --,m.id_Tabla
	  ,m.Clave 'MACROTUNEL'
	  ,t.Clave 'TABLA'
	  ,[id_Entrega] 'ID ENTREGA'
  FROM [ArandanosDB].[dbo].[COSECHA] c
  inner join RECOLECTOR r on r.id_Recolector = c.id_Recolector
  inner join MACROTUNEL m on m.id_Macrotunel = c.id_Macrotunel
  inner join TABLA t on m.id_Tabla = t.id_Tabla
