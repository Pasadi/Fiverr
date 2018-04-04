import java.text.DecimalFormat;

/**
 * EQPoly.java is the super class since it contains methods that are common to
 * both the triangle and quadrilateral class.
 * It takes coordinate points from the point class and has methods that 
 * calculate length between points and list all vertices.
 *
 */
// all attributes for this class are declared here
public class EQPoly {
	public  String name;
	public EQPoint vert1,vert2,vert3;
	public double side1,side2,side3;
 	public final double EPSILON;




	// the constructor assigns values to attributes declared. 
	public EQPoly(String name, EQPoint p1,EQPoint p2, EQPoint p3){
		this.name=name;
		this.vert1=p1;
		this.vert2=p2;
		this.vert3=p3;
		side1=sideLength(vert1,vert3);
		side2=sideLength(vert2,vert3);
		side3=sideLength(vert1,vert2);
		this.EPSILON=0.0001;

}
	// we will calculate area to check for collinear points
	protected double computeArea(){
		double area =Math.abs((vert1.getX()*(vert2.getY()-vert3.getY()) + vert2.getX()*(vert3.getY()-vert1.getY()) + vert3.getX()*(vert1.getY()-vert2.getY()))*0.5);
		DecimalFormat df = new DecimalFormat("0.000");
		System.out.println("Computing Area from Poly Class is %f : "+df.format(area));
		return area;
	}
	//need an accessor method to get the private area field
	public boolean isCollinear(){
		if(computeArea() == 0)
			return true;
		return false;
	}
	// compute the length for each side of figure using the distance formular
	public double sideLength(EQPoint x,EQPoint y){
		double side= Math.sqrt(Math.pow(y.getX()-x.getX(), 2)+Math.pow(y.getY()-x.getY(), 2));
		return Math.round(side*100.0)/100.0;
	}
	// first string in line will be read as name, so we will display the name and type of polygon
	public String PrintName(String Polytype,String name){
		//output.println("The name of this "+ Polytype+" is "+name);
		return"The name of this "+ Polytype+" is "+name;
	}
	// get values from file and arrange the as coordinate points
	public String listVertices(){
	double x,y,x1,y1,x2,y2;
	x= vert1.getX(); y=vert1.getY(); 
	x1=vert2.getX(); y1=vert2.getY();
	x2=vert3.getX(); y2=vert3.getY();
	return "Vertices: ("+x+","+y+") ("+x1+","+y1+") ("+x2+","+y2+")";
}
	//display length of sides as a string
	public String listSides(){
		return "Side1 is: " +side1+"\nSide2 is: " +side2+"\nSide3 is: " +side3;
		

	}
	
}


