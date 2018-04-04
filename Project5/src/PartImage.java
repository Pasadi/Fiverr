import javafx.geometry.Point2D;
public class PartImage {
    private boolean[][] pixels;
    private boolean[][] visited;
    private int rows;
    private int cols;

    public PartImage(int r, int c) {
        rows = r;
        cols = c;
        visited = new boolean[r][c];
        pixels = new boolean[r][c];
    }

    public PartImage(int rw, int cl, byte[][] data) {
        this(rw,cl);
        for (int r=0; r<10; r++) {
            for (int c=0; c<10; c++) {
                if (data[r][c] == 1)
                    pixels[r][c] = true;
                else
                    pixels[r][c]= false;
            }
        }
        duplicateOriginalArray();
    }

    public void duplicateOriginalArray() { //Everytime this function is called pixels array will get copied to visited array
        for (int r=0; r<pixels.length; r++) {
            for (int c=0; c<pixels.length; c++) {
                if (pixels[r][c] == true)
                    visited[r][c] = true;
                else
                    visited[r][c]= false;
            }
        }
    }

    public int getRows()
    {
        return rows;
    }
    public int getCols() {
        return cols;
    }
    public boolean getPixel(int r, int c) {
        return pixels[r][c];
    }

    public void print() {
         for (int r=0; r<pixels.length; r++) {
             for (int c=0; c<pixels.length; c++) {
                 if (visited[r][c] == true)
                     System.out.print("*");
                 else
                     System.out.print("-");
             }
             System.out.println();
         }
     }

    public Point2D findStart() {
        for (int r=0; r<pixels.length; r++) {
            for (int c=0; c<pixels.length; c++) {
                if (pixels[r][c] == true) //return Point2d Object when the first black pixel is encountered
                    return new Point2D(r,c);
            }
        }
        return null;
    }

    public int partSize() {
        int partSize = 0;
        for (int r=0; r<visited.length; r++) {
            for (int c=0; c<visited[0].length; c++) {
                if (visited[r][c] == true)
                    partSize++;
            }
        }
        return partSize;
    }

    private boolean withinBounds(int r, int c)
    {
       if((0<=r) && (r<pixels.length) && (0<=c) && (c<pixels[0].length))
           return true;
       return false;
    }

    /**
     * input parameters :
     * r = row no. c = column no.
     * description :
     * given a black pixel, the function will attempt to traverse all neighbouring the pixels in all the 8 directions (north,northeast,east,southeeast...)
     * when a black pixel is encountered, it will be marked as white so that it wont be analyzed again
     * if a white or a already visited black node is encountered, the further traverse starting from that pixel will be stopped
     * Once the function ends, all the joining black pixels will be marked as white.
     * Broken : isPartSize!=0 . Hence if still there are black pixels remaining after one connecting traverse the picture is considered as broken
     * return :
     * none
     */
    private void expandFrom(int r, int c)
    {
        if(withinBounds(r,c) == false)
            return;

        if(visited[r][c] == false)
            return;

        if(visited[r][c] == true)
            visited[r][c] = false;

        expandFrom(r-1,c-1);
        expandFrom(r-1,c);
        expandFrom(r-1,c+1);
        expandFrom(r,c+1);
        expandFrom(r+1,c+1);
        expandFrom(r+1,c);
        expandFrom(r+1,c-1);
        expandFrom(r,c-1);
    }

    /**
     * input parameters :
     * r = row no. c = column no.
     * description :
     * 4 is the no of edges that a black block will contribute to in computing perimeter when it is not surrounded by any black blocks in any direction
     * Considered directions : up,down,left,right
     * Likewise if a black box is surrounded by 4 black boxes, it will contribute 0 ; 3 black boxes , it will contribute 1 ;
     * 2 black boxes , 2 ; 1 black box , 3 ; 0 black boxes , 4.
     * When a black box is encountered it will be turned in to a white box. In other words it wont be examined again. visited array will be used for this purpose
     * In each recursion the pixel specified by r,c will only be examined if its within bounds of the array and only if it is not a white box (or a previous black box now marked as a white to make sure its not being considered in calculating parameter again)
     * Hence ' 4 - noOfBlackBoxes its surrounded by = contribution of the black box at position r,c for the perimeter'
     * Recursively the function will traverse in all the nodes in all the 4 directions.
     * the answer of the neighbouring boxes perimeter count will be cumulated, and the contribution of the particular node to the perimeter will also be added at each recursive call
     * return :
     * perimeter of black pixels
     *
     */
    private int perimeterOf(int r, int c) {

        int noOfNeighbours = 0;
        int perimeter = 0;

        if (withinBounds(r, c) == false)
            return 0;

        if (visited[r][c] == false)
            return 0;

        if (visited[r][c] == true)
            visited[r][c] = false;

        if (withinBounds(r + 1, c) && pixels[r + 1][c] == true) {
            perimeter += perimeterOf(r + 1, c);
            noOfNeighbours++;
        }
        if (withinBounds(r, c + 1) && pixels[r][c + 1] == true) {
            perimeter += perimeterOf(r, c + 1);
            noOfNeighbours++;
        }
        if (withinBounds(r - 1, c) && pixels[r - 1][c] == true) {
            perimeter += perimeterOf(r - 1, c);
            noOfNeighbours++;
        }
        if (withinBounds(r, c - 1) && pixels[r][c - 1] == true) {
            perimeter += perimeterOf(r, c - 1);
            noOfNeighbours++;
        }

        return perimeter + (4 - noOfNeighbours);
    }

    public boolean isBroken(){
        Point2D p = findStart();
        partSize();
        expandFrom((int)p.getX(), (int)p.getY());
        return (partSize() != 0);
    }

    public int perimeter() {
        duplicateOriginalArray();
        Point2D p = findStart();
        return perimeterOf((int)p.getX(), (int)p.getY());
    }

    public static PartImage exampleA() {
        byte[][] pix = {{0,0,0,0,0,0,0,0,0,0},
            {0,1,1,1,1,1,1,0,0,0},
            {0,1,1,1,1,1,1,0,0,0},
            {0,1,1,1,1,1,1,1,1,0},
            {0,0,0,1,1,1,1,1,1,0},
            {0,1,1,1,1,1,1,1,1,0},
            {0,1,1,1,1,1,1,1,1,0},
            {0,1,1,1,1,1,1,0,0,0},
            {0,0,0,0,1,1,1,0,0,0},
            {0,0,0,0,0,0,0,0,0,0}};
        return new PartImage(10,10, pix);
    }

    public static PartImage exampleB() {
        byte[][] pix = {{1,0,1,0,1,0,1,0,0,0},
            {1,0,1,0,1,0,1,1,1,1},
            {1,0,1,0,1,0,1,0,0,0},
            {1,0,1,0,1,0,1,1,1,1},
            {1,0,1,0,1,0,1,0,0,0},
            {1,0,1,0,1,0,1,1,1,1},
            {1,1,1,1,1,1,1,0,0,0},
            {0,1,0,1,0,0,1,1,1,1},
            {0,1,0,1,0,0,1,0,0,0},
            {0,1,0,1,0,0,1,0,0,0}};
        return new PartImage(10,10, pix);
    }

    public static PartImage exampleC() {
        byte[][] pix = {{1,1,1,0,0,0,1,0,0,0},
            {1,1,1,1,0,0,1,1,1,0},
            {1,1,1,1,1,1,1,1,1,1},
            {0,1,1,1,0,0,1,0,0,0},
            {0,0,1,0,0,0,0,0,0,0},
            {1,0,0,0,1,1,0,1,1,1},
            {1,1,0,1,1,1,1,1,1,1},
            {1,1,1,1,1,1,1,1,1,1},
            {0,0,1,1,0,1,1,1,1,1},
            {0,0,1,0,0,0,1,1,0,0}};
        return new PartImage(10,10, pix);
    }

    public static PartImage exampleD() {
        byte[][] pix = {{1,0,1,0,1,0,1,1,0,0},
            {1,0,1,0,0,0,1,0,0,0},
            {0,0,0,0,0,0,0,0,1,1},
            {1,0,1,1,1,1,1,1,1,0},
            {1,0,0,1,0,0,1,0,0,0},
            {1,1,0,0,0,1,1,0,0,1},
            {0,1,0,0,0,0,0,0,1,1},
            {0,1,0,1,0,0,0,0,0,0},
            {0,0,0,1,1,1,0,0,0,0},
            {0,0,0,0,0,1,1,0,0,0}};
        return new PartImage(10,10, pix);
    }
}