///**
// * Created by pasadim on 4/1/2018.
// */
//import PhoneBookPkg.Person;
//
//import java.util.*;
//
//class Node implements Comparator<Node> {
//    String name;
//    String n;
//    Node(String name, String n)
//    {
//        this.name = name;
//        this.n = n;
//    }
//
//    @Override
//    public int compare(Node O,Node O2) //When adding to the List which is sorted using this approach, it will
//    {
//        int result = 0;
//
//        return result = this.n.compareTo(O.n);
//    }
//    @Override
//    public boolean equals(Object o) //When adding to the List which is sorted using this approach, it will
//    {
//        return (this.n.equals(((Node)o).n));
//
//    }
//
//    public int compareTo(Node o2) {
//        return this.n.compareTo(o2.n);
//    }
//}
//public class Tester {
//
//    public static Comparator<Node> TempComparator = new Comparator<Node>() { //Used to sort the sortedListByNumber by Person.getNumber()
//
//        @Override
//        public int compare(Node o1, Node o2) {
//            System.out.println("Comparing o1 : "+ o1.n + " o2 : "+o2.n);
//
//            return o1.n.compareTo(o2.n);
//        }
//    };
//
//    public static void main(String args[]) {
//        Comparator<Node> priorityCompare;
//        // create arraylist
//
//            TreeMap<String, Object> tmpMap = new TreeMap<String, Object>(new Comparator<String>(){
//                @Override
//                public int compare(String key1, String key2) {
//                    //logic for comparing dates
//                    return 1;
//                }
//            });
//
//        LinkedHashMap<Node,Node> duplicateFilter = new LinkedHashMap<Node,Node>(priorityCompare);
//        LinkedHashMap<Node,Node> lst = new LinkedHashMap<Node,Node>((Map<? extends Node, ? extends Node>) TempComparator);
//
//
//        new Comparator<Node>() {
//            @Override
//            public int compare(Node o1, Node o2) {
//                return o1.n.compareTo(o2.n);
//            }
//        });
//        List<Node> tmp = new ArrayList<Node>();
//
//        Node a = new Node("AAA","1");
//        Node b = new Node("CCC","3");
//        Node d = new Node("DDD","0");
//        Node c = new Node("BBB","2");
//
//        tmp.add(a);
//        tmp.add(b);
//        tmp.add(d);
//        tmp.add(c);
//   //     Collections.sort(tmp);
//        for(Node t : tmp)
//        {
//            System.out.println("Printing Elements"+t.n);
//            lst.add(t);
//        }
//
//        for(Node m:lst){
//            System.out.println("Printing LInked List : "+m.n); //maintains insertion  order
//        }
//
//
//        // search for key 'TUTORIALS' with natural ordering
//        int index = Collections.binarySearch(lst,new Node("BBB","2"));
//
//        System.out.println("'2' is available at index: "+index);
//
//        for(Node m:lst){
//            System.out.println("Printing LInked List : "+m.n); //maintains insertion  order
//        }
//    }
//
//}
