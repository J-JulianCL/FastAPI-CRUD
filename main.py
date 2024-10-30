from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Configuración de la base de datos SQLite
# Utilizamos SQLite como base de datos y configuramos SQLAlchemy para manejar las conexiones
DATABASE_URL = "sqlite:///./taller.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo de datos de la base de datos
class Alumno(Base):
    """
    Modelo de SQLAlchemy que representa la tabla de alumnos en la base de datos.
    Contiene los campos:
    - id: Identificador único del alumno
    - nombre: Nombre del alumno
    - semestre: Semestre en el que está inscrito el alumno
    - activo: Estado de actividad del alumno (True si es actual, False si es de semestres anteriores)
    """
    __tablename__ = "alumnos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    semestre = Column(Integer)
    activo = Column(Boolean, default=True)

# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Iniciar la aplicación de FastAPI
app = FastAPI()

# Modelos Pydantic para validación y respuesta en la API
class AlumnoCreate(BaseModel):
    """
    Modelo de entrada para crear o actualizar un alumno.
    """
    nombre: str
    semestre: int
    activo: bool = True

class AlumnoResponse(AlumnoCreate):
    """
    Modelo de respuesta que incluye el ID del alumno.
    """
    id: int

# Dependencia para obtener la sesión de la base de datos
def get_db():
    """
    Generador de sesiones de la base de datos.
    Asegura que cada solicitud obtiene su propia sesión y se cierra al final.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# CRUD Endpoints

@app.post("/alumnos/", response_model=AlumnoResponse)
def crear_alumno(alumno: AlumnoCreate, db: Session = Depends(get_db)):
    """
    Crear un nuevo alumno en la base de datos.
    - **alumno**: Datos del alumno a crear (nombre, semestre, activo).
    - **db**: Sesión de la base de datos (proporcionada por la dependencia).
    - **Retorna**: El alumno creado con su ID asignado.
    """
    db_alumno = Alumno(nombre=alumno.nombre, semestre=alumno.semestre, activo=alumno.activo)
    db.add(db_alumno)
    db.commit()
    db.refresh(db_alumno)
    return db_alumno

@app.get("/alumnos/{alumno_id}", response_model=AlumnoResponse)
def leer_alumno(alumno_id: int, db: Session = Depends(get_db)):
    """
    Obtener un alumno específico por su ID.
    - **alumno_id**: ID del alumno a obtener.
    - **db**: Sesión de la base de datos.
    - **Retorna**: Los datos del alumno si se encuentra, o un error 404 si no existe.
    """
    alumno = db.query(Alumno).filter(Alumno.id == alumno_id).first()
    if alumno is None:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")
    return alumno

@app.get("/alumnos/", response_model=list[AlumnoResponse])
def leer_alumnos(activo: bool = True, db: Session = Depends(get_db)):
    """
    Obtener una lista de alumnos, filtrando por estado de actividad.
    - **activo**: Filtra por alumnos activos o inactivos (True para activos, False para inactivos).
    - **db**: Sesión de la base de datos.
    - **Retorna**: Una lista de alumnos que cumplen con el filtro.
    """
    alumnos = db.query(Alumno).filter(Alumno.activo == activo).all()
    return alumnos

@app.put("/alumnos/{alumno_id}", response_model=AlumnoResponse)
def actualizar_alumno(alumno_id: int, alumno: AlumnoCreate, db: Session = Depends(get_db)):
    """
    Actualizar los datos de un alumno existente.
    - **alumno_id**: ID del alumno a actualizar.
    - **alumno**: Datos nuevos para actualizar (nombre, semestre, activo).
    - **db**: Sesión de la base de datos.
    - **Retorna**: El alumno actualizado o un error 404 si no se encuentra.
    """
    db_alumno = db.query(Alumno).filter(Alumno.id == alumno_id).first()
    if db_alumno is None:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")
    db_alumno.nombre = alumno.nombre
    db_alumno.semestre = alumno.semestre
    db_alumno.activo = alumno.activo
    db.commit()
    db.refresh(db_alumno)
    return db_alumno

@app.delete("/alumnos/{alumno_id}")
def eliminar_alumno(alumno_id: int, db: Session = Depends(get_db)):
    """
    Eliminar un alumno por su ID.
    - **alumno_id**: ID del alumno a eliminar.
    - **db**: Sesión de la base de datos.
    - **Retorna**: Un mensaje de confirmación o un error 404 si no se encuentra.
    """
    alumno = db.query(Alumno).filter(Alumno.id == alumno_id).first()
    if alumno is None:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")
    db.delete(alumno)
    db.commit()
    return {"detail": "Alumno eliminado"}