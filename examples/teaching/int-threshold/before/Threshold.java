package teaching;

// Self-built teaching case, not a real-project effectiveness experiment.
public class Threshold {
    public static int decide(int score, String label) {
        int current;
        current = score;
        if (current > 5) {
            return 1;
        }
        return 0;
    }
}
