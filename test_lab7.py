import book
import pytest
import user
import library


@pytest.fixture
def library_init():
    book1 = book.Book("El alquimista", "Paulo Cohelo", 1967, "ISBN001")
    miguel = user.User("Miguel", "ID001")

    library1 = library.Library()
    library1.add_book(book1)
    library1.add_user(miguel)

    return library1


@pytest.fixture
def library_full():
    """Biblioteca con 2 libros y 2 usuarios para integración y sistema."""
    library1 = library.Library()
    library1.add_book(book.Book("El alquimista", "Paulo Cohelo", 1967, "ISBN001"))
    library1.add_book(book.Book("Harry potter", "J.K Rowling", 1995, "ISBN002"))
    library1.add_user(user.User("Miguel", "ID001"))
    library1.add_user(user.User("Max", "ID002"))
    return library1


@pytest.mark.unit
def test_borrow_book():
    book1 = book.Book("El alquimista", "Paulo Cohelo", 1967, "ISBN001")
    assert book1.title == "El alquimista"
    book1.borrow()
    assert book1.borrowed == True


@pytest.mark.unit
def test_re_borrow_book():
    book1 = book.Book("El alquimista", "Paulo Cohelo", 1967, "ISBN001")
    assert book1.title == "El alquimista"
    book1.borrow()
    assert book1.borrowed == True
    with pytest.raises(ValueError, match="The book is already borrowed"):
        book1.borrow()


@pytest.mark.unit
def test_borrow_return_book():
    book1 = book.Book("El alquimista", "Paulo Cohelo", 1967, "ISBN001")
    assert book1.title == "El alquimista"
    book1.borrow()
    assert book1.borrowed == True
    book1.return_book()
    assert book1.borrowed == False


@pytest.mark.unit
def test_return_book_not_borrowed():
    book1 = book.Book("El alquimista", "Paulo Cohelo", 1967, "ISBN001")
    with pytest.raises(ValueError, match="The book is not currently borrowed"):
        book1.return_book()


@pytest.mark.unit
def test_user_register_borrow_and_return():
    miguel = user.User("Miguel", "ID001")
    book1 = book.Book("El alquimista", "Paulo Cohelo", 1967, "ISBN001")
    assert miguel.get_history() == []
    miguel.register_borrow(book1)
    miguel.register_return(book1)
    history = miguel.get_history()
    assert len(history) == 2
    assert history[0].endswith("El alquimista")
    assert history[1].endswith("El alquimista")


@pytest.mark.integration
def test_library_borrow_fixture(library_init):
    library1 = library_init

    library1.borrow_book("ID001", "ISBN001")
    assert library1.books[0].borrowed == True
    assert len(library1.users[0].get_history()) == 1


@pytest.mark.integration
def test_library_borrow_already_borrowed_book(library_full):
    library1 = library_full

    library1.borrow_book("ID001", "ISBN001")
    with pytest.raises(ValueError, match="The book is already borrowed"):
        library1.borrow_book("ID002", "ISBN001")

    # El segundo usuario no debe quedar con registro de préstamo
    assert library1.users[1].get_history() == []


@pytest.mark.integration
def test_library_return_then_borrow_other_user(library_full):
    library1 = library_full

    library1.borrow_book("ID001", "ISBN001")
    library1.return_book("ID001", "ISBN001")
    assert library1.books[0].borrowed == False

    library1.borrow_book("ID002", "ISBN001")
    assert library1.books[0].borrowed == True
    assert len(library1.users[0].get_history()) == 2
    assert len(library1.users[1].get_history()) == 1


@pytest.mark.system
def test_system_full_loan_cycle(library_full):
    """Flujo completo: préstamos, rechazo, devoluciones y nuevo préstamo."""
    library1 = library_full
    alquimista, harry = library1.books

    # 1. Miguel pide prestado El alquimista
    library1.borrow_book("ID001", "ISBN001")
    assert alquimista.borrowed == True

    # 2. Max intenta el mismo libro y es rechazado
    with pytest.raises(ValueError, match="The book is already borrowed"):
        library1.borrow_book("ID002", "ISBN001")

    # 3. Max pide prestado Harry Potter (disponible)
    library1.borrow_book("ID002", "ISBN002")
    assert harry.borrowed == True

    # 4. Miguel devuelve El alquimista
    library1.return_book("ID001", "ISBN001")
    assert alquimista.borrowed == False

    # 5. Max pide prestado El alquimista, ahora disponible
    library1.borrow_book("ID002", "ISBN001")
    assert alquimista.borrowed == True

    # Estado final del sistema
    assert len(library1.users[0].get_history()) == 2   # Miguel: préstamo + devolución
    assert len(library1.users[1].get_history()) == 2   # Max: Harry Potter + El alquimista


@pytest.mark.system
def test_system_error_handling(library_full, monkeypatch):
    """Flujo de errores controlados sin alterar el estado de la biblioteca."""
    library1 = library_full

    # 1. Usuario inexistente
    with pytest.raises(ValueError, match="User not found"):
        library1.borrow_book("ID999", "ISBN001")

    # 2. Libro inexistente
    with pytest.raises(ValueError, match="Book not found"):
        library1.borrow_book("ID001", "ISBN999")

    # 3. Devolver un libro que no está prestado
    with pytest.raises(ValueError, match="The book is not currently borrowed"):
        library1.return_book("ID001", "ISBN001")

    # 4. Préstamos deshabilitados: no se presta y no se registra historial
    monkeypatch.setitem(library.settings, "loans_enabled", False)
    library1.borrow_book("ID001", "ISBN001")
    assert library1.books[0].borrowed == False
    assert library1.users[0].get_history() == []

    # 5. Al habilitar préstamos el sistema vuelve a operar con normalidad
    monkeypatch.setitem(library.settings, "loans_enabled", True)
    library1.borrow_book("ID001", "ISBN001")
    assert library1.books[0].borrowed == True