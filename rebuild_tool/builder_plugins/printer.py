from rebuild_tool import builder

class RealBuilder(builder.Builder):
    

    @builder.check_build
    def build(self, pkgs, verbose=True):
        for pkg in pkgs:
            print(pkg)
        return True
