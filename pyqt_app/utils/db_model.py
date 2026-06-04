import os
import re
import string
import secrets
import logging
from datetime import datetime

import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool
import bcrypt
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("iutepi.db_model")


class DatabaseModel:
    def __init__(self):
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'iutepi_sgla'),
            'use_pure': True,
        }
        self.pool = None

    def _init_pool(self):
        if self.pool is not None:
            return
        try:
            self.pool = MySQLConnectionPool(
                pool_name="iutepi_pool",
                pool_size=5,
                **self.config
            )
        except Exception as e:
            logger.error("No se pudo crear pool de conexiones: %s", e)
            self.pool = None

    def conectar(self):
        if self.pool is None:
            self._init_pool()
        if self.pool:
            try:
                return self.pool.get_connection()
            except Exception as e:
                logger.warning("Pool de conexiones fallo, usando conexion directa: %s", e)
        return mysql.connector.connect(**self.config)

    # ========== SEGURIDAD ==========

    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')

    @staticmethod
    def check_password(password, hashed):
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'), hashed.encode('utf-8')
            )
        except (ValueError, TypeError) as e:
            logger.warning("check_password fallo (hash invalido): %s", e)
            return False

    @staticmethod
    def _generar_password_aleatoria(longitud=16):
        alfabeto = string.ascii_letters + string.digits + "!@#$%&*"
        return ''.join(secrets.choice(alfabeto) for _ in range(longitud))

    @staticmethod
    def _guardar_credenciales_iniciales(nombre_usuario, password):
        ruta = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "PRIMER_LOGIN.txt"
        )
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(f"Usuario: {nombre_usuario}\n")
                f.write(f"Password: {password}\n")
                f.write(f"Generado: {datetime.now().isoformat()}\n")
                f.write("IMPORTANTE: Cambie esta contrasena despues del primer inicio de sesion.\n")
            logger.warning("Credenciales iniciales guardadas en %s", ruta)
        except OSError as e:
            logger.exception("No se pudo escribir archivo de credenciales: %s", e)

    @staticmethod
    def validar_nombre_usuario(nombre):
        return bool(re.match(r'^[a-zA-Z0-9_]{3,50}$', nombre))

    @staticmethod
    def validar_contrasena(contrasena):
        return len(contrasena) >= 6

    # ========== INICIALIZACIÓN ==========

    def inicializar_usuarios(self):
        conn = self.conectar()
        if not conn:
            return False
        try:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
                    nombre_usuario VARCHAR(50) UNIQUE NOT NULL,
                    contrasena VARCHAR(255) NOT NULL,
                    rol ENUM('Admin', 'Profesor') NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS semestres (
                    id_semestre INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(50) NOT NULL,
                    periodo VARCHAR(20) DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS horarios_semestrales (
                    id_horario INT AUTO_INCREMENT PRIMARY KEY,
                    id_semestre INT NOT NULL,
                    materia VARCHAR(100) NOT NULL,
                    profesor VARCHAR(100) NOT NULL,
                    dia_semana VARCHAR(20) NOT NULL,
                    hora_inicio TIME NOT NULL,
                    hora_fin TIME NOT NULL,
                    seccion VARCHAR(20) DEFAULT '',
                    FOREIGN KEY (id_semestre) REFERENCES semestres(id_semestre) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS laboratorios (
                    id_lab INT AUTO_INCREMENT PRIMARY KEY,
                    nombre_lab VARCHAR(100) NOT NULL UNIQUE,
                    tipo VARCHAR(50) DEFAULT '',
                    capacidad INT DEFAULT 0,
                    estatus VARCHAR(20) DEFAULT 'Disponible'
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS docentes (
                    id_docente INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL UNIQUE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reservas (
                    id_reserva INT AUTO_INCREMENT PRIMARY KEY,
                    id_docente INT NOT NULL,
                    materia VARCHAR(100),
                    carrera VARCHAR(100),
                    num_estudiantes INT DEFAULT 0,
                    periodo VARCHAR(20),
                    tipo_reserva VARCHAR(50),
                    FOREIGN KEY (id_docente) REFERENCES docentes(id_docente) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detalles_horario (
                    id_detalle INT AUTO_INCREMENT PRIMARY KEY,
                    id_reserva INT NOT NULL,
                    id_lab INT NOT NULL,
                    dia_semana VARCHAR(20) DEFAULT '',
                    fecha DATE NOT NULL,
                    hora_inicio TIME NOT NULL,
                    hora_fin TIME NOT NULL,
                    FOREIGN KEY (id_reserva) REFERENCES reservas(id_reserva) ON DELETE CASCADE,
                    FOREIGN KEY (id_lab) REFERENCES laboratorios(id_lab) ON DELETE CASCADE
                )
            """)

            cursor.execute("SELECT 1 FROM usuarios WHERE nombre_usuario = 'admin'")
            admin_row = cursor.fetchone()
            if not admin_row:
                password_inicial = self._generar_password_aleatoria()
                hashed = self.hash_password(password_inicial)
                cursor.execute(
                    "INSERT INTO usuarios (nombre_usuario, contrasena, rol) VALUES (%s, %s, %s)",
                    ('admin', hashed, 'Admin')
                )
                self._guardar_credenciales_iniciales('admin', password_inicial)

            cursor.execute("SELECT COUNT(*) FROM semestres")
            count_row = cursor.fetchone()
            if (count_row is None or count_row[0] == 0):
                for i in range(1, 7):
                    cursor.execute(
                        "INSERT INTO semestres (nombre, periodo) VALUES (%s, %s)",
                        (str(i), "")
                    )

            cursor.execute("SELECT COUNT(*) FROM laboratorios")
            count_row = cursor.fetchone()
            if (count_row is None or count_row[0] == 0):
                labs = [
                    ("Laboratorio I", "Laboratorio", 30),
                    ("Laboratorio II", "Laboratorio", 25),
                    ("Laboratorio III", "Laboratorio", 30),
                    ("Laboratorio IV", "Laboratorio", 25),
                ]
                for nombre, tipo, cap in labs:
                    cursor.execute(
                        "INSERT INTO laboratorios (nombre_lab, tipo, capacidad) VALUES (%s, %s, %s)",
                        (nombre, tipo, cap)
                    )
            else:
                cursor.execute(
                    "UPDATE laboratorios SET nombre_lab = 'Laboratorio IV' "
                    "WHERE nombre_lab = 'Laboratorio VI'"
                )

            conn.commit()
            return True
        except Exception as e:
            logger.error("Error inicializando: %s", e)
            return False
        finally:
            conn.close()

    # ========== USUARIOS ==========

    def validar_usuario(self, nombre, contrasena):
        conn = self.conectar()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id_usuario, contrasena, rol FROM usuarios WHERE nombre_usuario = %s",
                (nombre,)
            )
            res = cursor.fetchone()
            if not res:
                return None
            user_id, stored_hash, rol = res

            if not stored_hash or not stored_hash.startswith('$2'):
                logger.warning(
                    "Usuario id=%s tiene contrasena en formato invalido; "
                    "rechazando login (requiere reset manual).", user_id
                )
                return None

            if self.check_password(contrasena, stored_hash):
                return rol

            return None
        except Exception:
            logger.exception("Error validando usuario id_buscado=%s", nombre)
            return None
        finally:
            conn.close()

    def crear_usuario(self, nombre_usuario, contrasena, rol):
        conn = self.conectar()
        if not conn:
            return False, "Error de conexión"
        try:
            if not self.validar_nombre_usuario(nombre_usuario):
                return False, "Usuario debe tener 3-50 caracteres alfanuméricos"
            if not self.validar_contrasena(contrasena):
                return False, "Contraseña debe tener al menos 6 caracteres"

            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM usuarios WHERE nombre_usuario = %s", (nombre_usuario,))
            if cursor.fetchone():
                return False, "El usuario ya existe"

            hashed = self.hash_password(contrasena)
            cursor.execute(
                "INSERT INTO usuarios (nombre_usuario, contrasena, rol) VALUES (%s, %s, %s)",
                (nombre_usuario, hashed, rol)
            )
            conn.commit()
            return True, "Usuario creado correctamente"
        except Exception as e:
            logger.error("Error creando usuario: %s", e)
            return False, f"Error: {e}"
        finally:
            conn.close()

    def obtener_usuarios(self):
        conn = self.conectar()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id_usuario, nombre_usuario, rol FROM usuarios")
            return cursor.fetchall()
        finally:
            conn.close()

    def eliminar_usuario(self, id_usuario):
        conn = self.conectar()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT nombre_usuario FROM usuarios WHERE id_usuario = %s", (id_usuario,))
            res = cursor.fetchone()
            if res and res[0] == 'admin':
                return False
            cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s", (id_usuario,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error("Error eliminando usuario: %s", e)
            return False
        finally:
            conn.close()

    # ========== DOCENTES ==========

    def obtener_docente_por_nombre(self, nombre):
        conn = self.conectar()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id_docente FROM docentes WHERE nombre = %s", (nombre,))
            res = cursor.fetchone()
            return res[0] if res else None
        finally:
            conn.close()

    def crear_docente(self, nombre):
        conn = self.conectar()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO docentes (nombre) VALUES (%s)", (nombre,))
            conn.commit()
            return cursor.lastrowid
        except mysql.connector.IntegrityError:
            cursor.execute("SELECT id_docente FROM docentes WHERE nombre = %s", (nombre,))
            res = cursor.fetchone()
            return res[0] if res else None
        except Exception as e:
            logger.error("Error al crear docente: %s", e)
            return None
        finally:
            conn.close()

    # ========== RESERVAS ==========

    def verificar_disponibilidad(self, id_lab, fecha, h_inicio, h_fin, conn=None):
        cerrar = conn is None
        if cerrar:
            conn = self.conectar()
        if not conn:
            return False, "Error de conexión"
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*)
                FROM detalles_horario dh
                JOIN reservas r ON dh.id_reserva = r.id_reserva
                WHERE dh.id_lab = %s AND dh.fecha = %s
                AND dh.hora_inicio < %s AND dh.hora_fin > %s
            """, (id_lab, fecha, h_fin, h_inicio))
            count_row = cursor.fetchone()
            count = count_row[0] if count_row is not None else 0
            if count > 0:
                return False, "El laboratorio ya está reservado en ese horario"
            return True, ""
        except Exception as e:
            logger.error("Error verificando disponibilidad: %s", e)
            return False, str(e)
        finally:
            if cerrar:
                conn.close()

    def guardar_reserva(self, datos):
        conn = self.conectar()
        if not conn:
            return False
        try:
            disponible, msg = self.verificar_disponibilidad(
                datos['id_lab'], datos['fecha'],
                datos['h_inicio'], datos['h_fin'], conn
            )
            if not disponible:
                logger.warning("Reserva no disponible: %s", msg)
                return False

            id_doc = self.crear_docente(datos['profesor'])
            if not id_doc:
                logger.error("No se pudo crear/encontrar docente: %s", datos['profesor'])
                return False

            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reservas (id_docente, materia, carrera, num_estudiantes, periodo, tipo_reserva, seccion)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (id_doc, datos['materia'], datos['carrera'],
                  datos['estudiantes'], datos['periodo'], datos['tipo'],
                  datos.get('seccion', '')))
            id_res = cursor.lastrowid

            cursor.execute("""
                INSERT INTO detalles_horario (id_reserva, dia_semana, fecha, hora_inicio, hora_fin, id_lab)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (id_res, datos.get('dia', ''), datos['fecha'],
                  datos['h_inicio'], datos['h_fin'], datos['id_lab']))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error("Error guardando reserva: %s", e)
            return False
        finally:
            conn.close()

    def actualizar_reserva(self, id_reserva, datos):
        conn = self.conectar()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE reservas
                SET materia=%s, num_estudiantes=%s, carrera=%s, periodo=%s, tipo_reserva=%s, seccion=%s
                WHERE id_reserva=%s
            """, (datos['materia'], datos['estudiantes'], datos.get('carrera', ''),
                  datos.get('periodo', ''), datos.get('tipo', 'Clase Semestral'),
                  datos.get('seccion', ''), id_reserva))

            cursor.execute("""
                UPDATE detalles_horario
                SET id_lab=%s, fecha=%s, hora_inicio=%s, hora_fin=%s, dia_semana=%s
                WHERE id_reserva=%s
            """, (datos.get('id_lab'), datos.get('fecha'), datos.get('h_inicio'),
                  datos.get('h_fin'), datos.get('dia', ''), id_reserva))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error("Error actualizando reserva: %s", e)
            return False
        finally:
            conn.close()

    def eliminar_reserva(self, id_reserva):
        conn = self.conectar()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM detalles_horario WHERE id_reserva = %s", (id_reserva,))
            cursor.execute("DELETE FROM reservas WHERE id_reserva = %s", (id_reserva,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error("Error al eliminar reserva: %s", e)
            return False
        finally:
            conn.close()

    def obtener_reservas_por_fecha(self, fecha_sql):
        conn = self.conectar()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TIME_FORMAT(dh.hora_inicio, '%H:%i'), d.nombre, r.materia,
                       r.carrera, r.num_estudiantes, l.nombre_lab, dh.dia_semana
                FROM reservas r
                JOIN docentes d ON r.id_docente = d.id_docente
                JOIN detalles_horario dh ON r.id_reserva = dh.id_reserva
                JOIN laboratorios l ON dh.id_lab = l.id_lab
                WHERE dh.fecha = %s
                ORDER BY dh.hora_inicio ASC
            """, (fecha_sql,))
            return cursor.fetchall()
        finally:
            conn.close()

    def obtener_todas_reservas(self, limite=50):
        conn = self.conectar()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.id_reserva, d.nombre, r.materia, r.carrera, r.num_estudiantes,
                       l.nombre_lab, dh.fecha, TIME_FORMAT(dh.hora_inicio, '%H:%i'),
                       TIME_FORMAT(dh.hora_fin, '%H:%i'), r.seccion
                FROM reservas r
                JOIN docentes d ON r.id_docente = d.id_docente
                JOIN detalles_horario dh ON r.id_reserva = dh.id_reserva
                JOIN laboratorios l ON dh.id_lab = l.id_lab
                ORDER BY dh.fecha DESC, dh.hora_inicio ASC
                LIMIT %s
            """, (limite,))
            return cursor.fetchall()
        finally:
            conn.close()

    def obtener_estadisticas_detalladas(self):
        conn = self.conectar()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT l.nombre_lab, l.tipo,
                    COUNT(CASE WHEN r.tipo_reserva = 'Clase Semestral' THEN 1 END),
                    COUNT(CASE WHEN r.tipo_reserva = 'Evento Único' THEN 1 END)
                FROM laboratorios l
                LEFT JOIN detalles_horario dh ON l.id_lab = dh.id_lab
                LEFT JOIN reservas r ON dh.id_reserva = r.id_reserva
                GROUP BY l.id_lab
            """)
            return cursor.fetchall()
        finally:
            conn.close()

    def obtener_reservas_por_lab(self, id_lab):
        conn = self.conectar()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.id_reserva, d.nombre, r.materia, r.carrera, r.num_estudiantes,
                       r.periodo, dh.fecha, dh.hora_inicio, dh.hora_fin, dh.dia_semana
                FROM reservas r
                JOIN docentes d ON r.id_docente = d.id_docente
                JOIN detalles_horario dh ON r.id_reserva = dh.id_reserva
                WHERE dh.id_lab = %s
                ORDER BY dh.fecha DESC, dh.hora_inicio
            """, (id_lab,))
            return cursor.fetchall()
        finally:
            conn.close()

    def obtener_estadisticas_generales(self):
        conn = self.conectar()
        if not conn:
            return (0, 0)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), COALESCE(SUM(capacidad), 0) FROM laboratorios")
            res = cursor.fetchone()
            return res if res else (0, 0)
        finally:
            conn.close()

    # ========== LABORATORIOS ==========

    def obtener_espacios(self):
        conn = self.conectar()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id_lab, nombre_lab, tipo, capacidad, estatus FROM laboratorios"
            )
            return cursor.fetchall()
        finally:
            conn.close()

    def actualizar_estatus_laboratorio(self, id_lab, nuevo_estatus):
        conn = self.conectar()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE laboratorios SET estatus = %s WHERE id_lab = %s",
                (nuevo_estatus, id_lab)
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error("Error actualizando estatus: %s", e)
            return False
        finally:
            conn.close()

    def obtener_datos_analiticas_ocupacion(self):
        conn = self.conectar()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT l.nombre_lab, COUNT(dh.id_reserva) as total
                FROM laboratorios l
                LEFT JOIN detalles_horario dh ON l.id_lab = dh.id_lab
                GROUP BY l.id_lab
            """)
            return cursor.fetchall()
        finally:
            conn.close()

    def obtener_datos_analiticas_carreras(self):
        conn = self.conectar()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(carrera, 'Sin asignar') as carrera, COUNT(*) as total
                FROM reservas
                GROUP BY carrera
            """)
            return cursor.fetchall()
        finally:
            conn.close()

    # ========== SEMESTRES ==========

    def obtener_semestres(self):
        conn = self.conectar()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id_semestre, nombre, periodo FROM semestres ORDER BY id_semestre"
            )
            return cursor.fetchall()
        finally:
            conn.close()

    def actualizar_periodo_semestre(self, id_semestre, periodo):
        conn = self.conectar()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE semestres SET periodo = %s WHERE id_semestre = %s",
                (periodo, id_semestre)
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error("Error actualizando período: %s", e)
            return False
        finally:
            conn.close()

    def obtener_horarios_semestrales(self, id_semestre):
        conn = self.conectar()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id_horario, materia, profesor, dia_semana, hora_inicio, hora_fin, seccion
                FROM horarios_semestrales
                WHERE id_semestre = %s
                ORDER BY hora_inicio
            """, (id_semestre,))
            return cursor.fetchall()
        finally:
            conn.close()

    def obtener_horarios_por_dias(self, id_semestre, dias):
        if not dias:
            return []
        conn = self.conectar()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            placeholders = ", ".join(["%s"] * len(dias))
            cursor.execute(f"""
                SELECT id_horario, materia, profesor, dia_semana, hora_inicio, hora_fin, seccion
                FROM horarios_semestrales
                WHERE id_semestre = %s
                AND UPPER(dia_semana) IN ({placeholders})
                ORDER BY hora_inicio
            """, (id_semestre, *[d.upper() for d in dias]))
            return cursor.fetchall()
        finally:
            conn.close()

    def agregar_horario_semestral(self, id_semestre, materia, profesor, dia_semana,
                                   hora_inicio, hora_fin, seccion=""):
        conn = self.conectar()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO horarios_semestrales
                    (id_semestre, materia, profesor, dia_semana, hora_inicio, hora_fin, seccion)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (id_semestre, materia, profesor, dia_semana, hora_inicio, hora_fin, seccion))
            conn.commit()
            return True
        except Exception as e:
            logger.error("Error agregando horario: %s", e)
            return False
        finally:
            conn.close()

    def eliminar_horario_semestral(self, id_horario):
        conn = self.conectar()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM horarios_semestrales WHERE id_horario = %s",
                (id_horario,)
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error("Error eliminando horario: %s", e)
            return False
        finally:
            conn.close()
