import book 
import pytest
import user
import library

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

@pytest.fixture
def library_init():
    book1 = book.Book("El alquimista", "Paulo Cohelo", 1967, "ISBN001")
    miguel = user.User("Miguel","ID001")
    book2 = book.Book("Harry potter", "J.K Rowling", 1995, "ISBN002")
    enrique = user.User("Max","ID002")
    library1 = library.Library()

    library1.add_book(book1, book2)
    library1.add_user(miguel, enrique)

    return library1


@pytest.mark.wip
def test_library_borrow_fixture(library_init):

    library1=library_init
    
    library1.borrow_book("ID001", "ISBN001")
    assert library1.books[0].borrowed == True



