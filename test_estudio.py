"""
GUIA DE ESTUDIO - Examen practico de pytest
Sistema de biblioteca (book.py, user.py, library.py).
Cada seccion = un tema de la guia. Ejecuta todo con:  pytest -v
"""
import book
import library
import pytest
import user


# ------------------------------------------------------------------
# FIXTURES (tema 7)
# ------------------------------------------------------------------
@pytest.fixture
def libro():
    """Dato que se repetia en varias pruebas: el libro de ejemplo."""
    return book.Book("El alquimista", "Paulo Cohelo", 1967, "ISBN001")


@pytest.fixture
def library_full():
    """Biblioteca con 2 libros y 2 usuarios."""
    lib = library.Library()
    lib.add_book(book.Book("El alquimista", "Paulo Cohelo", 1967, "ISBN001"))
    lib.add_book(book.Book("Harry potter", "J.K Rowling", 1995, "ISBN002"))
    lib.add_user(user.User("Miguel", "ID001"))
    lib.add_user(user.User("Max", "ID002"))
    return lib


@pytest.fixture
def library_catalog():
    """Biblioteca con 3 libros (para parametrize)."""
    lib = library.Library()
    lib.add_book(book.Book("El alquimista", "Paulo Cohelo", 1967, "ISBN001"))
    lib.add_book(book.Book("Harry potter", "J.K Rowling", 1995, "ISBN002"))
    lib.add_book(book.Book("Don Quijote", "Cervantes", 1605, "ISBN003"))
    return lib


# ------------------------------------------------------------------
# TEMA 1 - monkeypatch.setattr()
# Sustituir una funcion/atributo por un valor controlado.
# ------------------------------------------------------------------
@pytest.mark.prestamos
def test_tema1_setattr(library_full, monkeypatch):
    """
    Que decir: reemplazo Library._find_book por una funcion falsa que siempre
    devuelve un libro que YO controlo, asi pruebo borrow_book sin depender de
    los libros reales de la biblioteca. monkeypatch deshace el cambio al terminar.
    """
    libro_falso = book.Book("Libro Falso", "Nadie", 2000, "FAKE")
    monkeypatch.setattr(library.Library, "_find_book", lambda self, isbn: libro_falso)

    library_full.borrow_book("ID001", "CUALQUIER-ISBN")

    assert libro_falso.borrowed is True
    assert library_full.users[0].get_history()[0].endswith("Libro Falso")


# ------------------------------------------------------------------
# TEMA 2 - monkeypatch.delattr()
# Eliminar temporalmente un atributo y ver que pasa.
# ------------------------------------------------------------------
def test_tema2_delattr(libro, monkeypatch):
    """
    Que decir: borro el atributo 'borrowed' de la instancia. borrow() lo lee
    (self.borrowed), asi que al no existir debe lanzar AttributeError.
    Compruebo ese comportamiento con pytest.raises.
    """
    monkeypatch.delattr(libro, "borrowed")

    with pytest.raises(AttributeError):
        libro.borrow()


# ------------------------------------------------------------------
# TEMA 3 - monkeypatch.setitem()
# Cambiar un valor de un diccionario de configuracion.
# ------------------------------------------------------------------
@pytest.mark.wip
def test_tema3_setitem(library_full, monkeypatch):
    """
    Que decir: library.settings es un diccionario de configuracion. Con setitem
    cambio SOLO la llave "loans_enabled" a False; borrow_book debe usar el nuevo
    valor y no prestar el libro. Al terminar, pytest restaura el valor original.
    """
    monkeypatch.setitem(library.settings, "loans_enabled", False)

    library_full.borrow_book("ID001", "ISBN001")

    assert library_full.books[0].borrowed is False


# ------------------------------------------------------------------
# TEMA 4 y 5 - pytest.ini + marcadores
# pytest.ini ya registra:  prestamos: pruebas relacionadas con prestamos
# Dos pruebas: una marcada y otra no.
# Comandos:
#   pytest -v -m prestamos          -> solo las marcadas (incluye tema1 y la de abajo)
#   pytest -v -m "not prestamos"    -> todas las demas
#   pytest -v -m unit               -> solo las unitarias
# ------------------------------------------------------------------
@pytest.mark.prestamos
def test_tema4_marcador_prestamos(library_full):
    """Que decir: registre el marcador 'prestamos' en pytest.ini y lo aplique con
    @pytest.mark.prestamos; asi filtro con  pytest -m prestamos."""
    library_full.borrow_book("ID001", "ISBN001")
    assert library_full.books[0].borrowed is True


def test_tema5_sin_marcador(libro):
    """Esta NO tiene marcador: no se ejecuta con  pytest -m prestamos."""
    assert libro.borrowed is False


# ------------------------------------------------------------------
# TEMA 6 - parametrize
# Una sola funcion de prueba, tres entradas con su resultado esperado.
# ------------------------------------------------------------------
@pytest.mark.parametrize(
    "isbn, titulo_esperado",
    [
        ("ISBN001", "El alquimista"),
        ("ISBN002", "Harry potter"),
        ("ISBN003", "Don Quijote"),
    ],
)
def test_tema6_parametrize(library_catalog, isbn, titulo_esperado):
    """Que decir: en vez de escribir 3 pruebas casi iguales, defino los datos de
    entrada (isbn) y el resultado esperado (titulo) y pytest ejecuta 3 casos."""
    assert library_catalog._find_book(isbn).title == titulo_esperado


# ------------------------------------------------------------------
# TEMA 7 - fixtures
# La fixture 'libro' reemplaza el Book(...) repetido; la piden 2 pruebas.
# ------------------------------------------------------------------
@pytest.mark.unit
def test_tema7_fixture_borrow(libro):
    """Que decir: la fixture se pide como argumento; pytest la crea y la inyecta."""
    libro.borrow()
    assert libro.borrowed is True


@pytest.mark.unit
def test_tema7_fixture_return(libro):
    libro.borrow()
    libro.return_book()
    assert libro.borrowed is False


# ------------------------------------------------------------------
# TEMA 8 - cobertura de caja blanca
# 1) pytest --cov=library --cov-report=term-missing
# 2) El reporte lista las lineas que NO se ejecutaron (columna Missing).
#    Antes de estas pruebas faltaban: 36-40 (return_book) y 53 (Book not found).
# 3) Estas pruebas hacen que se ejecuten.
# ------------------------------------------------------------------
def test_tema8_cobertura_return_book(library_full):
    """Cubre las lineas 36-40 de library.py (return_book)."""
    library_full.borrow_book("ID001", "ISBN001")
    library_full.return_book("ID001", "ISBN001")
    assert library_full.books[0].borrowed is False


def test_tema8_cobertura_libro_inexistente(library_full):
    """Cubre la linea 53 de library.py (raise 'Book not found')."""
    with pytest.raises(ValueError, match="Book not found"):
        library_full._find_book("ISBN999")


# ------------------------------------------------------------------
# TEMA 9 - pytest.raises()
# ------------------------------------------------------------------
def test_tema9_raises_usuario_inexistente(library_full):
    """Que decir: la entrada invalida es un user_id que no existe. Espero un
    ValueError con el mensaje 'User not found'; pytest.raises pasa solo si se
    lanza esa excepcion (y match revisa el mensaje)."""
    with pytest.raises(ValueError, match="User not found"):
        library_full.borrow_book("ID999", "ISBN001")


def test_tema9_raises_libro_ya_prestado(library_full):
    library_full.borrow_book("ID001", "ISBN001")
    with pytest.raises(ValueError, match="already borrowed"):
        library_full.borrow_book("ID002", "ISBN001")


# ------------------------------------------------------------------
# TEMA 10 - try-except
# Library.safe_borrow CAPTURA ValueError y devuelve un mensaje.
# Cualquier otra excepcion se PROPAGA.
# ------------------------------------------------------------------
def test_tema10_excepcion_capturada(library_full):
    """Excepcion CAPTURADA: safe_borrow no lanza nada, devuelve el mensaje."""
    resultado = library_full.safe_borrow("ID999", "ISBN001")
    assert resultado == "Error: User not found"


def test_tema10_exito_sin_excepcion(library_full):
    assert library_full.safe_borrow("ID001", "ISBN001") == "Loan registered"


def test_tema10_excepcion_que_se_propaga(library_full, monkeypatch):
    """Excepcion que SE PROPAGA: quito 'settings' del modulo; borrow_book lanza
    NameError, que NO es ValueError, asi que el except no la atrapa y llega a la prueba."""
    monkeypatch.delattr(library, "settings")
    with pytest.raises(NameError):
        library_full.safe_borrow("ID001", "ISBN001")


# ------------------------------------------------------------------
# TEMA 11 - capsys
# ------------------------------------------------------------------
def test_tema11_capsys(library_full, monkeypatch, capsys):
    """Que decir: con loans_enabled=False, borrow_book imprime 'Loans are disabled'.
    capsys captura lo impreso; capsys.readouterr() devuelve un objeto y .out es
    el texto de stdout (incluye el salto de linea del print)."""
    monkeypatch.setitem(library.settings, "loans_enabled", False)

    library_full.borrow_book("ID001", "ISBN001")

    captured = capsys.readouterr()
    assert captured.out == "Loans are disabled\n"