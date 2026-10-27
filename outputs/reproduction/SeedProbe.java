public class SeedProbe {
  public static void main(String[] args) {
    org.evosuite.Properties.getInstance();
    System.out.println("CONFIGURED_RANDOM_SEED="+org.evosuite.Properties.RANDOM_SEED);
    System.out.println("ACTUAL_RANDOM_SEED="+org.evosuite.utils.Randomness.getSeed());
  }
}
