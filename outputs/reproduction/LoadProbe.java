import java.lang.reflect.*;
public class LoadProbe {
  public static void main(String[] args) throws Exception {
    Class<?> c=Class.forName("org.apache.commons.lang.BooleanUtils");
    System.out.println("CLASS_SOURCE="+c.getProtectionDomain().getCodeSource().getLocation());
    System.out.println("CLASS_RESOURCE="+c.getResource("BooleanUtils.class"));
    Method m=c.getMethod("toBoolean",String.class);
    for(String s:args) {
      try { System.out.println("INPUT="+s+" RETURN="+m.invoke(null,s)); }
      catch(InvocationTargetException e) { System.out.println("INPUT="+s+" THREW="+e.getCause().getClass().getName()+":"+e.getCause().getMessage()); }
    }
  }
}
