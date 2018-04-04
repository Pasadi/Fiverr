
public class EQPoint {
		private double x;
		private double y;

		//construct new point with given x and y
		public EQPoint(double x, double y){
			this.x=x;
			this.y=y;
		}
		//return given x value
		public double getX(){
			return x;
		}
		//return given y value
		public double getY(){
			return y;
		}
		//test whether the points given are duplicates
		public boolean equals(EQPoint p1){
			if(this.x==p1.getX() && this.y==p1.getY()){
				return true;
			}
				else{
					return false;
				}
				
			}
		}




