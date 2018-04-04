
	public class PolyException extends Exception {
		String polytype;
		String EXtype;
		static final long  serialVersionUID=42L;
		PolyException(String EXtype,String polytype)
		{
			super();
			this.EXtype=EXtype;
			this.polytype=polytype;
			
		}
		public String getMessage(String points)
		{
			return "This line containing "+points+" are "+EXtype+" and do not form a "+polytype+"\n";
		}
	}



