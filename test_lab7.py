
# Importamos las clases y pytest para realizar pruebas
import book
import pytest
import user, library


# Fixture que crea una biblioteca con un libro y un usuario
@pytest.fixture
def library_init():
    book1 = book.Book("El alquimista", 'Paulo Coehlo', 1967, 'ISBN0001')
    miguel = user.User('Miguel', 'ID001')
    lib = library.Library()
    lib.add_book(book1)   # Agrega el libro
    lib.add_user(miguel)  # Agrega el usuario
    return lib            # Devuelve la biblioteca preparada


# Prueba que un libro se pueda prestar
@pytest.mark.unit
def test_borrow_book():
    book1 = book.Book("El alquimista", 'Paulo Coehlo', 1967, 'ISBN0001')
    assert book1.title == 'El alquimista'  # Verifica el título
    book1.borrow()                        # Presta el libro
    assert book1.borrowed == True         # Comprueba que esté prestado


# Prueba que no se pueda prestar dos veces el mismo libro
@pytest.mark.unit
def test_re_borrow_book():
    book1 = book.Book("El alquimista", 'Paulo Coehlo', 1967, 'ISBN0001')
    assert book1.title == 'El alquimista'
    book1.borrow()                 # Primer préstamo
    assert book1.borrowed == True

    # Espera un ValueError al intentar prestarlo otra vez
    with pytest.raises(ValueError, match="The book is already borrowed"):
        book1.borrow()


# Prueba que un libro se pueda prestar y devolver
@pytest.mark.unit
def test_borrow_and_return_book():
    book1 = book.Book("El alquimista", 'Paulo Coehlo', 1967, 'ISBN0001')
    assert book1.title == 'El alquimista'
    book1.borrow()                         # Presta el libro
    assert book1.borrowed == True
    book1.return_book()                    # Devuelve el libro
    assert book1.borrowed == False         # Verifica que ya no esté prestado


# Prueba el préstamo de un libro desde la biblioteca
@pytest.mark.unit
def test_library_borrow():
    book1 = book.Book("El alquimista", 'Paulo Coehlo', 1967, 'ISBN0001')
    miguel = user.User('Miguel', 'ID001')
    lib = library.Library()

    lib.add_book(book1)                    # Agrega el libro
    assert lib.books[0].title == "El alquimista"

    lib.add_user(miguel)                   # Agrega el usuario
    assert lib.users[0].name == "Miguel"

    lib.borrow_book('ID001', 'ISBN0001')   # Realiza el préstamo
    assert book1.borrowed == True          # Verifica el préstamo


# Prueba un préstamo utilizando el fixture
@pytest.mark.wip
def test_library_borrow_fixture(library_init):
    lib = library_init                    # Usa la biblioteca preparada
    assert lib.users[0].name == "Miguel"
    lib.borrow_book('ID001', 'ISBN0001')  # Presta el libro
    assert lib.books[0].borrowed == True


# Prueba reemplazar temporalmente un método con monkeypatch
@pytest.mark.unit
def test_borrow_setattr(monkeypatch, library_init):
    lib = library_init
    libro = lib.books[0]

    # Función falsa que siempre devuelve el mismo libro
    def buscar_falso(isbn):
        return libro

    # Sustituye temporalmente el método de búsqueda
    monkeypatch.setattr(lib, "_find_book", buscar_falso)

    lib.borrow_book("ID001", "cualquier isbn")
    assert libro.borrowed == True   # Verifica que se prestó


# Prueba qué sucede si eliminamos el método borrow
@pytest.mark.unit
def test_borrow_delattr(monkeypatch, library_init):
    monkeypatch.delattr(book.Book, "borrow")  # Elimina temporalmente el método

    # Comprueba que se genere un AttributeError
    with pytest.raises(AttributeError):
        library_init.borrow_book('ID001', 'ISBN0001')


# Prueba que no se presten libros si los préstamos están desactivados
@pytest.mark.unit
def test_loans_disabled_setitem(monkeypatch, library_init):
    # Desactiva temporalmente los préstamos
    monkeypatch.setitem(library.settings, "loans_enabled", False)

    library_init.borrow_book('ID001', 'ISBN0001')  # Intenta prestar

    assert library_init.books[0].borrowed == False  # No se prestó
    assert library_init.users[0].get_history() == []  # Historial vacío


# Prueba diferentes ISBN sin repetir el código del test
@pytest.mark.unit
@pytest.mark.parametrize("isbn, titulo_esperado", [
    ("ISBN001", "1984"),
    ("ISBN002", "Moby Dick"),
    ("ISBN003", "War and Peace"),
])
def test_find_book_parametrize(isbn, titulo_esperado):
    lib = library.Library()

    # Agrega tres libros a la biblioteca
    lib.add_book(book.Book("1984", "George Orwell", 1949, "ISBN001"))
    lib.add_book(book.Book("Moby Dick", "Herman Melville", 1851, "ISBN002"))
    lib.add_book(book.Book("War and Peace", "Leo Tolstoy", 1869, "ISBN003"))

    # Verifica que cada ISBN corresponda al título esperado
    assert lib._find_book(isbn).title == titulo_esperado


# Prueba el mensaje cuando los préstamos están desactivados
@pytest.mark.unit
def test_loans_disabled_capsys(monkeypatch, capsys, library_init):
    # Desactiva los préstamos
    monkeypatch.setitem(library.settings, "loans_enabled", False)

    library_init.borrow_book('ID001', 'ISBN0001')

    captured = capsys.readouterr()  # Captura lo impreso

    # Verifica que el mensaje mostrado sea correcto
    assert captured.out == "Loans are disabled\n"


# Prueba que se pueda devolver un libro
@pytest.mark.unit
def test_library_return_book(library_init):
    library_init.borrow_book('ID001', 'ISBN0001')  # Presta el libro
    library_init.return_book('ID001', 'ISBN0001')  # Devuelve el libro

    assert library_init.books[0].borrowed == False  # Ya no está prestado

    # Verifica que existan dos movimientos en el historial
    assert len(library_init.users[0].get_history()) == 2


# Prueba la búsqueda de un usuario inexistente
@pytest.mark.unit
def test_find_user_not_found(library_init):

    # Espera un ValueError porque el usuario no existe
    with pytest.raises(ValueError, match="User not found"):
        library_init._find_user('ID999')
