package PhoneBookPkg;

public class Person implements Comparable<Person>{

    String firstName;
    String lastName;
    String number;

    public Person(String lastName, String firstName, String number)
    {
        this.firstName=firstName;
        this.lastName=lastName;
        this.number=number;
    }

    @Override
    public int compareTo(Person O) //When adding to the List which is sorted using this approach, it will
    {
        int result = 0;

        if ((result = this.lastName.compareTo(O.lastName)) != 0) //first check if an entry exists in the list with the same last name. If not sort accordingly
            return result;
        else
            result = this.firstName.compareTo(O.firstName); //if the same last name exists, then compare the firsnt names and sort accordingly
        return result;
    }
    public String getFirstName() {
        return firstName;
    }

    public void setFirstName(String firstName) {
        this.firstName = firstName;
    }

    public String getLastName() {
        return lastName;
    }

    public void setLastName(String lastName) {
        this.lastName = lastName;
    }

    public String getNumber() {
        return number;
    }

    public void setNumber(String number) {
        this.number = number;
    }

}
