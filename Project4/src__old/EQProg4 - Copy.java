import java.io.File;
import java.io.FileNotFoundException;
import java.io.*;
import java.util.ArrayList;
import java.util.Scanner;
import java.util.StringTokenizer;

public class EQProg4 {
	public static void main(String args[]) throws FileNotFoundException{
		// read through the file and extract first word on line as name of triangle
		// extrat numbers on each line to form coordinate points that make a triangle
		Scanner inputfile=new Scanner(new File("polyInput.txt"));
		 PrintStream output = new PrintStream(new File("EQmyPoly.txt"));

		String a= "", line=""; 
		 while(inputfile.hasNextLine()){
			 line=inputfile.nextLine();
			 a=line;
		
			StringTokenizer st=new StringTokenizer(a);
			while(st.hasMoreElements()){
				
// if a line has 7 elements, it has a name as first string and 3-coordinate points
//therefore it forms a triangle				
 if(st.countTokens()==7){
	 String name=st.nextToken();
	 double x=Double.parseDouble(st.nextToken());
		double y=Double.parseDouble(st.nextToken());
		double x1=Double.parseDouble(st.nextToken());
		double y1=Double.parseDouble(st.nextToken());
		double x2=Double.parseDouble(st.nextToken());
		double y2=Double.parseDouble(st.nextToken());
		EQPoint p1=new EQPoint(x,y);
		 EQPoint p2=new EQPoint(x1,y1);
		 EQPoint p3=new EQPoint(x2,y2);
// we create a new instance of a triangle		 
 EQTriangle triangle1=new EQTriangle(name,p1,p2,p3);
 //put as many instances as we can have into an array list
 ArrayList<EQTriangle> mytriangle=new ArrayList<EQTriangle>();
 mytriangle.add(triangle1);
 
 // we will check to see if the points from a line and colinear
 //and we will throw and exception if it is
 try{ 
	 if(triangle1.isCollinear()== true){// throw exception it it doesnt
					throw new PolyException("Collinear","Triangle");
	 }
	 // if the line has duplicate points, we will throw another exception
	if(p1.equals(p2)||p2.equals(p3)||p1.equals(p3)){
		throw new PolyException("Duplicates","Triangle");

				}
	 
	 else{ // display the ff properties if it does
	System.out.println(triangle1.PrintName("triangle",name));
	output.println(triangle1.PrintName("triangle",name));
	System.out.println(triangle1.listVertices());
	output.println(triangle1.listVertices());
	System.out.println(triangle1.listSides());
	output.println(triangle1.listSides());;
	System.out.println(triangle1.listDiagonals());
	output.print(triangle1.listDiagonals());
	System.out.println(triangle1.checkSides());
	output.println(triangle1.checkSides());
	output.println();
	System.out.println();
	 }
 }
	 catch (PolyException e)

	 {
		 System.out.println(e.getMessage( triangle1.listVertices()));
		 output.println(e.getMessage( triangle1.listVertices()));
	 }
	 
	 }

 
 else{ // is a line has more than 7 elements, it will form a quadrilateral
	// read through the file and extract first word on line as name of triangle
			// extrat numbers on each line to form coordinate points that make a quad
	 
	 String name=st.nextToken();

	 double x=Double.parseDouble(st.nextToken());
		double y=Double.parseDouble(st.nextToken());
		double x1=Double.parseDouble(st.nextToken());
		double y1=Double.parseDouble(st.nextToken());
		double x2=Double.parseDouble(st.nextToken());
		double y2=Double.parseDouble(st.nextToken());
		double x3=Double.parseDouble(st.nextToken());
		double y3=Double.parseDouble(st.nextToken());
		EQPoint p1=new EQPoint(x,y);
		 EQPoint p2=new EQPoint(x1,y1);
		 EQPoint p3=new EQPoint(x2,y2);
		 EQPoint p4=new EQPoint(x3,y3);
		 
		// we create a new instance of a quad		 
	EQQuad quad=new EQQuad(name,p1,p2,p3,p4);
	
	 //put as many instances as we can have into an array list
	ArrayList<EQQuad> myQuad= new ArrayList<EQQuad>();
	
	 //now we will check to see if the points from a line and colinear
	 //and we will throw and exception if it is
	try{ 
		 if(quad.isCollinear()== true ){
						throw new PolyException("Collinear","Quadrilateral");
					}
		 // if the line has duplicate points, we will throw another exception

		 if(p1.equals(p2)||p2.equals(p3)||p1.equals(p3)||p3.equals(p4)||p1.equals(p4)){
				throw new PolyException("Duplicates","Quadrilateral");
		 
		 }
		 
		 // display all properties on both console and output file
	 myQuad.add(quad);
	 System.out.println(quad.PrintName("quadrilateral",name));
	 output.println(quad.PrintName("quadrilateral",name));
	 System.out.println(quad.listVertices());
	 output.println(quad.listVertices());
	 System.out.println(quad.listSides());
	 output.println(quad.listSides());
	 System.out.println(quad.listDiagonals());
	 output.println(quad.listDiagonals());
	 System.out.println(quad.checkSides());
	 output.println(quad.checkSides());
	 System.out.println();
	 output.println();

 }
			
 catch (PolyException e)

 {
	 //display exception message after catching exception
	 System.out.println(e.getMessage( quad.listVertices()));
	 output.println(e.getMessage( quad.listVertices()));
 }
 
 }
 
			}
 }
 		
}
	}



