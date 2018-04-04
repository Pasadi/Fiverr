package PhoneBookPkg;

import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.text.DecimalFormat;
import java.util.*;

public class PhoneBook {

    List<Person> sortedListByName = new ArrayList<>();
    List<Person> sortedListByNumber = new ArrayList<>();
    static PhoneBook phoneBook;
    static int dataSize= 0;
    public static void main(String[] args)
    {
        phoneBook = new PhoneBook();
        Scanner scanner = new Scanner(System.in);
        System.out.println("Starting Project......");
        System.out.println("Enable User Mode (Yes/No): ");
        String userMode = scanner.nextLine();
        if(userMode.equals("Yes"))
        {
            System.out.println(".......InitiateUserMode.......");

            InitiateUserMode();
        }
        else
        {
            InitiateTesterMode();
        }
    }

    public static void InitiateUserMode()
    {
        Scanner scanner = new Scanner(System.in);
        System.out.println("Enter Data Size: ");
        dataSize = scanner.nextInt();
        System.out.println("Your Data Size " + dataSize);
        PhoneBook.LoadData();
        phoneBook.sortedListByNumber.addAll(phoneBook.sortedListByName); // Copying the list sorted by name to the list that should be sorted by number
        Collections.sort(phoneBook.sortedListByNumber,NumberComparator); // Sort the list that should be sorted by number by the number
        System.out.println("Printing All Entries: " + dataSize);
        for(Person p : phoneBook.sortedListByNumber) {
            System.out.println(  p.getNumber()+ " , " + p.getLastName()+ " , " + p.getFirstName());
        }
        RunUserSearch();
    }
/*
*  Handles user and console interaction. User can speicfy which approach he wants to use for searching in each iteration
*  
* */
    public static void RunUserSearch()
    {
        System.out.println("Starting Search.....");
        Scanner scanner= new Scanner(System.in);
        while (true) {
            System.out.println("Use Search By Number ? (Yes/No): ");
            String searchByNumberApproach = scanner.nextLine();
            String key;
            int match = -1;
            List<Person> matchingEntries= new ArrayList<Person>();
            if(searchByNumberApproach.equals("Yes"))
            {
                System.out.println("Insert the Person's Phone Number : ");
                key = scanner.nextLine();
                match = PerformBinarySearch(phoneBook.sortedListByNumber, key, 0, phoneBook.sortedListByNumber.size() - 1, true); //Perform binary search on sortedListByNumber while matching People.getNumber() with the key
                if(match != -1)//Matches exist Get all the matching list
                {
                    matchingEntries = GetAllMatchingEntites(match,true,phoneBook.sortedListByNumber,key);
                }
            }
            else
            {
                System.out.println("Insert the Person's Last Name : ");
                String lastName = scanner.nextLine();
                System.out.println("Insert the Person's First Name : ");
                String firstName = scanner.nextLine();
                System.out.println("Searching Sorted-by-Name map for : " + lastName + " " + firstName); // full name should be provided for this approach
                key = lastName+firstName;
                match = PerformBinarySearch(phoneBook.sortedListByName, key, 0, phoneBook.sortedListByName.size() - 1, false); // sortedListByName will be searched for the provided full name while matching it wilth People.getLastName + People=getFirstName combination
                if(match != -1)//Matches exist Get all the matching list
                {
                    matchingEntries = GetAllMatchingEntites(match,false,phoneBook.sortedListByName,key);
                }

            }
            if (!matchingEntries.isEmpty()) {
                System.out.println("Printing Matches...");
                for(Person p : matchingEntries)
                {
                    System.out.println(p.getNumber() + " , " + p.getLastName() + " , " + p.getFirstName());

                }

            } else {
                System.out.println("No Match");

            }
            System.out.println("---------");
            System.out.println("Stop Search ? (Yes/No): ");
            String stop = scanner.nextLine();
            if(stop.equals("Yes")) {
                return;
            }
        }
    }

    private static List<Person> GetAllMatchingEntites(int matchIndex,boolean numSearch, List<Person> lst, String key) {
        List<Person> matches = new ArrayList<Person>();
        matches.add(lst.get(matchIndex));
        int down = matchIndex - 1;
        int up = matchIndex+1;


        String personProperty;
        while(down>=0)
        {
            if(numSearch) //If this is a search for the given number, then compare with the Person.getNumber value
            {
                personProperty = lst.get(down).getNumber();
            }
            else
            {
                personProperty = lst.get(down).getLastName()+lst.get(down).getFirstName();
            }
            if(personProperty.compareTo(key)!=0)
            {
                break; //no further matches. break;
            }
            else
            {
                matches.add(lst.get(down));//add lst.get(down);
                down-=1;
            }
        }
        while(up<lst.size())
        {
            if(numSearch) //If this is a search for the given number, then compare with the Person.getNumber value
            {
                personProperty = lst.get(up).getNumber();
            }
            else
            {
                personProperty = lst.get(up).getLastName()+lst.get(up).getFirstName();
            }
            if(personProperty.compareTo(key)!=0)
            {
                break;
            }
            else
            {
                matches.add(lst.get(up));//add lst.get(down);
                up+=1;
            }
        }

        return matches;

    }

    public static int PerformBinarySearch(List<Person> lst, String key, int min, int max, boolean numSearch)//false = name search, true number search
    {
            if (max < min)
                return -1;
            else {
                // calculate midpoint to cut set in half
                int mid = min + (max - min) / 2;

                 String personProperty;
                if(numSearch) //If this is a search for the given number, then compare with the Person.getNumber value
                {
                    personProperty = lst.get(mid).getNumber();
                }
                else
                {
                    personProperty = lst.get(mid).getLastName()+lst.get(mid).getFirstName(); //search for the fullname. Hence compare with getLastName()+getFirstName() combination
                }
                if (personProperty.compareTo(key) == 0) //Match exists
                {
                  return mid;
                }
                if (personProperty.compareTo(key) > 0) // key is in lower subset
                {
                    return PerformBinarySearch(lst, key, min, mid - 1, numSearch);
                } else if (personProperty.compareTo(key) < 0) { //key is in higher subset
                    return PerformBinarySearch(lst, key, mid + 1, max, numSearch);
                }
               return -1;
            }
    }
    public static void LoadData()//load data
    {
        List<String> lastNameList = new ArrayList<>(); //to store information read from the 3 files
        List<String> firstNameList = new ArrayList<>();
        List<String> areaCodeList = new ArrayList<>();

        LoadDataFromFile("LastNames.csv",lastNameList); //Load data from the specified file and put each entry in the file to the specified list
        LoadDataFromFile("FirstNames.csv", firstNameList);
        LoadDataFromFile("AreaCodes.csv", areaCodeList);

        System.out.println("Data Load Up is Complete .........");

        Random rand = new Random();
        String randomLastName =null;
        String randomFirstName =null;
        String randomAreaCode = null;
        String randomPhoneNumber = null;
        Person tmp = null;
        while(phoneBook.sortedListByName.size()<dataSize) { //follow the below procedure till the data set size specified by the user is reached
            int i = phoneBook.sortedListByName.size();
            while (i < dataSize) {
                randomLastName = lastNameList.get(rand.nextInt(lastNameList.size())); //get the random entry which is in the rand.nextInt() index value speciied
                randomFirstName = firstNameList.get(rand.nextInt(firstNameList.size()));
                randomAreaCode = areaCodeList.get(rand.nextInt(areaCodeList.size()));
                randomPhoneNumber = phoneBook.GeneratePhoneNumberGivenAreaCode(randomAreaCode); //generate phone number given area code
                tmp = new Person(randomLastName, randomFirstName, randomPhoneNumber);//create a person object with the randomly picked attributes

                phoneBook.sortedListByName.add(tmp); //add the entry to the list
                // To check pos dup removal phoneBook.sortedListByName.add(tmp);
                i++;
            }
            Collections.sort(phoneBook.sortedListByName); //sort the list (Person has implemented Comparable interface & compareTo method is implemented in Person class to make the sorting in lastname,firstnmae manner
            RemoveDuplicates(); //Remove duplicates
        }


    }

    public String GeneratePhoneNumberGivenAreaCode(String areaCode)
    {
        Random rand = new Random();
        int num2 = rand.nextInt(742)+1; //generate random numbers from 0 - 741 + 1 so that second set of 3 numbers lies in 1-742
        int num3 = rand.nextInt(10000);

        DecimalFormat df3 = new DecimalFormat("000"); // 3 zeros
        DecimalFormat df4 = new DecimalFormat("0000"); // 4 zeros

        String phoneNumber = areaCode + "-" + df3.format(num2) + "-" + df4.format(num3);
        return phoneNumber;
    }

    public static void RemoveDuplicates()
    {
        Set<Person> duplicateFilter = new TreeSet<Person>(new Comparator<Person>() { //this set will ensure that no Person object exists in the set which have identical 3 attributes
            @Override
            public int compare(Person o1, Person o2) {
                if(
                        (o1.getLastName().equalsIgnoreCase(o2.getLastName())) //if firstname lastname and number all are same then return 0 = not adding the entry to th set
                                && (o1.getFirstName().equalsIgnoreCase(o2.getFirstName()))
                                && (o1.getNumber().equalsIgnoreCase(o2.getNumber()))

                        ){
                    return 0;
                }
                return 1;
            }
        });
        duplicateFilter.addAll(phoneBook.sortedListByName); //add the elements in the list to the set which will remove duplicates as mentioned above
        phoneBook.sortedListByName.clear(); //clear the list
        phoneBook.sortedListByName.addAll(duplicateFilter); //add the entries in the filetered set back to the List
        Collections.sort(phoneBook.sortedListByName); //sort the list
    }

    public static void LoadDataFromFile(String fileName, List<String> tmpList)
    {
        String file = fileName;
        String []columns;
       // List<String> tmpList = new ArrayList<>();

        List<String[]> content = new ArrayList<>();
        BufferedReader br = null;
        try{
            br = new BufferedReader(new FileReader(file));
            String line = "";
            br.readLine();//ignore the first line as this is the header
            while ((line = br.readLine()) != null) {
                columns = line.split(","); //split if there are more than 1 column. We only need the first column as per all 3 files
                tmpList.add(columns[0]); //add the first column details to the list passed to the function
            }
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        } finally {
            if(br !=null)
                try {
                    br.close();
                }catch (IOException e) {
                    e.printStackTrace();
                }

        }
     }
    public static Comparator<Person> NumberComparator = new Comparator<Person>() { //Used to sort the sortedListByNumber by Person.getNumber()

        @Override
        public int compare(Person o1, Person o2) {
            return o1.getNumber().compareTo(o2.getNumber());
        }
    };

    public static void InitiateTesterMode()
    {
        System.out.println("....................Test Results..................");

        for(int i =0; i< 3;i++) { // DO the test 3 times
            dataSize = 1000;
            while (dataSize <= 1000000) { //multiple of 10 starting from 1000
                phoneBook.sortedListByNumber.clear();
                phoneBook.sortedListByName.clear();
                PhoneBook.LoadData();
                phoneBook.sortedListByNumber.addAll(phoneBook.sortedListByName);
                Collections.sort(phoneBook.sortedListByNumber, NumberComparator);
                RunTester();
                dataSize *= 10;
            }
        }
    }

    public static void RunTester()
    {
        System.out.println("Data Size : "+dataSize);
        List<String> testerForNumList = new ArrayList<>();
        List<String> testerForNameList = new ArrayList<>();
        Random rand = new Random();
        String Name =null;
        String Number =null;
        //Invalid data should also be searched to get worst time complexity
        testerForNameList.add("invalid");
        testerForNumList.add("0000");
        int i=0;
        while (i< 4) {
            Person randomPerson = phoneBook.sortedListByName.get(rand.nextInt(phoneBook.sortedListByName.size()));
            Name = randomPerson.getLastName() + randomPerson.getFirstName();
            Number = randomPerson.getNumber();
            testerForNameList.add(Name);
            testerForNumList.add(Number);
            i++;
        }

        long startTime =0;
        long elapsedTime = 0;
        long stopTime = 0;
        int matchIndex = -1;
        for(String number : testerForNumList)
        {
            startTime = System.nanoTime();
            matchIndex = PerformBinarySearch(phoneBook.sortedListByNumber, number, 0, phoneBook.sortedListByNumber.size() - 1, true);
            if(matchIndex != -1)
            {
                GetAllMatchingEntites(matchIndex,true,phoneBook.sortedListByNumber,number);
            }
            stopTime = System.nanoTime();
            elapsedTime += (stopTime - startTime);

        }
        for(String name : testerForNameList)
        {
            startTime = System.nanoTime();
            matchIndex = PerformBinarySearch(phoneBook.sortedListByName, name, 0, phoneBook.sortedListByName.size() - 1, false);
            if(matchIndex != -1)
            {
                GetAllMatchingEntites(matchIndex,false,phoneBook.sortedListByName,name);
            }
            stopTime = System.nanoTime();

            elapsedTime += (stopTime - startTime);

        }
        long avgTime = elapsedTime/(testerForNameList.size()+testerForNumList.size());
        System.out.println("Test Results for DataSize : "+dataSize + " Avg Search Time: "+avgTime);

    }
}


