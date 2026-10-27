import java.nio.file.*;
import java.util.Arrays;
import testgen.ClassUnderTestInstrumentor;
import testgen.InstrumentedClass;
// Verification harness only: uses the unchanged author's instrumentation API.
public class InstrumentReference {
  public static void main(String[] args) throws Exception {
    InstrumentedClass c = new ClassUnderTestInstrumentor()
        .getTestCaseInstrumentedClass(args[0], Arrays.asList("624,4"));
    Files.write(Paths.get(args[1]), c.getInstrumentedClassContent().getBytes("UTF-8"));
  }
}
