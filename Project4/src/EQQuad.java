import java.io.FileNotFoundException;

//this class inherits all public methods from EQpoly.java super class
// and attributes peculiar to this class are declared(ie.we add one more vertex for a quad).
public class EQQuad extends EQPoly {
	private EQPoint vert4;
	public double side4;
	public double diag1;
	public double diag2;

	// the constructor assigns values to attributes declared. 

public EQQuad(String name,EQPoint p1,EQPoint p2, EQPoint p3,EQPoint p4) throws FileNotFoundException{
	super(name, p1, p2, p3);
	this.vert4=p4;
	side4=sideLength(vert3,vert4);
	side3=sideLength(vert1,vert4);
	side1=sideLength(vert1,vert2);
	this.diag1=sideLength(vert1,vert3);
	this.diag2=sideLength(vert2,vert4);
}

//we override listVertices() method from super class since
// a quad has 4 vertices
public String listVertices(){
	double x,y,x1,y1,x2,y2,x3,y3;
	x= vert1.getX(); y=vert1.getY(); 
	x1=vert2.getX(); y1=vert2.getY();
	x2=vert3.getX(); y2=vert3.getY();
	x3=vert4.getX(); y3=vert4.getY();
	return "Vertices: ("+x+","+y+") ("+x1+","+y1+") ("+x2+","+y2+") ("+x3+","+y3+")";
}
//overridden method from super class to meet requirement of a quad
public String listSides(){
	return "Side1 is: " +side1+"\nSide2 is: " +side2+"\nSide3 is: " +side3+"\nSide4 is: "+side4;


}
// return the diagonals of the quad
public String listDiagonals(){
return "Diagonals  are: "+diag1+", "+diag2;
}

//we check if any of the sides has the same length
//comparism is done within an epsilon of 0.0001 
public String checkSides(){
	if(Math.abs(side1-side2)<=EPSILON||Math.abs(side2-side3)<=EPSILON||Math.abs(side3-side4)<=EPSILON||Math.abs(side1-side4)<=EPSILON)
	return  "At least two sides are of equal length";
	else{
	return "No sides are of equal length";
	}

}
	@Override
	public double computeArea(){
 		double area = Math.abs((vert1.getX()*(vert3.getY()-vert4.getY()) + vert3.getX()*(vert4.getY()-vert1.getY()) + vert4.getX()*(vert1.getY()-vert3.getY()))*0.5);

//		DecimalFormat df = new DecimalFormat("0.000");
//		System.out.println("Computing Area from Quad Class is %f : "+df.format(area));
		return area;
	}
	@Override
	public boolean isCollinear(){
		if(super.computeArea() == 0)
			return true;
		else if(this.computeArea() == 0)
			return true;
		return false;
	}
}