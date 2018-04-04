import java.io.FileNotFoundException;

//this class inherits all public methods from EQpoly.java super class
//and attributes peculiar to this class are declared
public class EQTriangle extends EQPoly {
	private double diag1;
	private double diag2;
	
	// the constructor assigns values to attributes declared. 

public EQTriangle(String name, EQPoint p1, EQPoint p2, EQPoint p3) throws FileNotFoundException {
		super(name, p1, p2, p3);
		this.diag1=sideLength(vert1,vert3);
		this.diag2=sideLength(vert1,vert2);
	}

//display the diagonals of the triangle
public String listDiagonals(){
	return "Diagonals  are: "+diag1+", "+diag2+"\n";

}

//we check if any of the sides has the same length
//comparism is done within an epsilon of 0.0001
public String checkSides(){
	if(Math.abs(side1-side2)<=EPSILON||Math.abs(side2-side3)<=EPSILON||Math.abs(side1-side3)<=EPSILON)
	return  "At least two sides are of equal length\n";
	else{
	return "No sides are of equal length\n";
}
}
}