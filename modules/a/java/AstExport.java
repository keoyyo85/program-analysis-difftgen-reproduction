import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.eclipse.jdt.core.*;
import org.eclipse.jdt.core.compiler.IProblem;
import org.eclipse.jdt.core.dom.*;

/** Read-only adapter over the author's existing Eclipse JDT jars. No target execution. */
public final class AstExport {
    private static CompilationUnit unit;
    private static Map<String,Object> obj(Object... entries) {
        Map<String,Object> r=new LinkedHashMap<String,Object>();
        for(int i=0;i<entries.length;i+=2) r.put((String)entries[i],entries[i+1]);
        return r;
    }
    private static Map<String,Object> span(ASTNode n) {
        int s=n.getStartPosition(), e=s+n.getLength(), last=Math.max(s,e-1);
        return obj("start_offset",s,"end_offset_exclusive",e,"start_line",unit.getLineNumber(s),
            "start_column",unit.getColumnNumber(s)+1,"end_line",unit.getLineNumber(last),
            "end_column",unit.getColumnNumber(last)+1);
    }
    private static Object tree(ASTNode n) {
        if(n==null) return null;
        Map<String,Object> r=obj("kind",n.getClass().getSimpleName(),"span",span(n));
        for(Object raw:n.structuralPropertiesForType()) {
            StructuralPropertyDescriptor d=(StructuralPropertyDescriptor)raw;
            if("javadoc".equals(d.getId())) continue;
            Object v=n.getStructuralProperty(d);
            if(v instanceof ASTNode) v=tree((ASTNode)v);
            else if(v instanceof List) {
                List<Object> values=new ArrayList<Object>();
                for(Object x:(List<?>)v) values.add(x instanceof ASTNode?tree((ASTNode)x):String.valueOf(x));
                v=values;
            } else if(v!=null && !(v instanceof Number) && !(v instanceof Boolean)) v=String.valueOf(v);
            r.put(d.getId(),v);
        }
        return r;
    }
    private static String type(String t) {return t.equals("String")?"java.lang.String":t;}
    private static String owner(MethodDeclaration m) {
        List<String> names=new ArrayList<String>();
        for(ASTNode n=m.getParent();n!=null;n=n.getParent()) {
            if(n instanceof AbstractTypeDeclaration) names.add(0,((AbstractTypeDeclaration)n).getName().getIdentifier());
        }
        String p=unit.getPackage()==null?"":unit.getPackage().getName().getFullyQualifiedName()+".";
        return p+String.join("$",names);
    }
    private static String json(Object x) {
        if(x==null) return "null";
        if(x instanceof Boolean || x instanceof Number) return x.toString();
        if(x instanceof Map) {
            List<String> parts=new ArrayList<String>();
            for(Object raw:((Map<?,?>)x).entrySet()) {
                Map.Entry<?,?> e=(Map.Entry<?,?>)raw;
                parts.add(json(e.getKey().toString())+":"+json(e.getValue()));
            }
            return "{"+String.join(",",parts)+"}";
        }
        if(x instanceof List) {
            List<String> parts=new ArrayList<String>();for(Object y:(List<?>)x) parts.add(json(y));
            return "["+String.join(",",parts)+"]";
        }
        StringBuilder b=new StringBuilder("\"");
        for(char c:x.toString().toCharArray()) {
            switch(c) {
                case '"':b.append("\\\"");break;case '\\':b.append("\\\\");break;
                case '\n':b.append("\\n");break;case '\r':b.append("\\r");break;case '\t':b.append("\\t");break;
                default: if(c<32 || Character.isSurrogate(c)) b.append(String.format("\\u%04x",(int)c));else b.append(c);
            }
        }
        return b.append('"').toString();
    }
    public static void main(String[] args) throws Exception {
        String source=new String(Files.readAllBytes(Paths.get(args[0])),StandardCharsets.UTF_8);
        ASTParser parser=ASTParser.newParser(AST.JLS4);
        parser.setKind(ASTParser.K_COMPILATION_UNIT);parser.setSource(source.toCharArray());
        Map<String,String> opts=new HashMap<String,String>();JavaCore.setComplianceOptions(JavaCore.VERSION_1_7,opts);
        parser.setCompilerOptions(opts);parser.setResolveBindings(false);parser.setStatementsRecovery(false);
        unit=(CompilationUnit)parser.createAST(null);
        List<Object> problems=new ArrayList<Object>();
        for(IProblem p:unit.getProblems()) if(p.isError()) problems.add(obj("line",p.getSourceLineNumber(),"message",p.getMessage()));
        final List<Object> methods=new ArrayList<Object>();
        unit.accept(new ASTVisitor() {
            @Override public boolean visit(MethodDeclaration m) {
                List<Object> params=new ArrayList<Object>();List<String> types=new ArrayList<String>();
                for(Object raw:m.parameters()) {
                    SingleVariableDeclaration p=(SingleVariableDeclaration)raw;
                    String t=p.getType().toString();
                    for(int i=0;i<p.getExtraDimensions();i++)t+="[]";
                    if(p.isVarargs())t+="[]";
                    if(t.startsWith("String["))t="java.lang."+t;
                    t=type(t);types.add(t);
                    params.add(obj("name",p.getName().getIdentifier(),"java_type",t,"varargs",p.isVarargs()));
                }
                String cls=owner(m),name=m.getName().getIdentifier();
                boolean statefulOwner=false;
                for(ASTNode at=m.getParent();at!=null;at=at.getParent()) {
                    if(at instanceof TypeDeclaration) {
                        TypeDeclaration td=(TypeDeclaration)at;
                        if(td.getFields().length>0 || td.getSuperclassType()!=null || !td.superInterfaceTypes().isEmpty())statefulOwner=true;
                    }
                }
                methods.add(obj("class_name",cls,"name",name,"signature",cls+"#"+name+"("+String.join(",",types)+")",
                    "parameters",params,"return_type",m.getReturnType2()==null?null:m.getReturnType2().toString(),
                    "is_static",Modifier.isStatic(m.getModifiers()),"constructor",m.isConstructor(),
                    "owner_has_fields_or_inheritance",statefulOwner,
                    "span",span(m),"body",tree(m.getBody())));
                return false;
            }
        });
        System.out.println(json(obj("parser","Eclipse JDT JLS4 / Java7 syntax (author lib)","errors",problems,"methods",methods)));
    }
}
