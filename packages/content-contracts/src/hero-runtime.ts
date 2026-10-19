/** Trusted build-time contracts; never loaded from portfolio content. */
import {createHeroResolver} from "./hero-resolution.ts";
import s0 from "../../../contracts/schemas/hero/hero-config.v1.json" with {type:"json"};
import s1 from "../../../contracts/schemas/hero/capabilities.v1.json" with {type:"json"};
import s2 from "../../../contracts/schemas/templates/documents/snapshot.v2.json" with {type:"json"};
import s3 from "../../../contracts/schemas/templates/documents/composition.v2.json" with {type:"json"};
import s4 from "../../../contracts/schemas/templates/documents/presentation.v2.json" with {type:"json"};
import s5 from "../../../contracts/schemas/templates/documents/customization.v2.json" with {type:"json"};
import s6 from "../../../contracts/schemas/templates/documents/content.v1.json" with {type:"json"};
import capabilities from "../../../contracts/hero/capabilities.v1.json" with {type:"json"};
export const heroResolver = createHeroResolver({schemas:{"hero/hero-config.v1.json":s0,"hero/capabilities.v1.json":s1,"templates/documents/snapshot.v2.json":s2,"templates/documents/composition.v2.json":s3,"templates/documents/presentation.v2.json":s4,"templates/documents/customization.v2.json":s5,"templates/documents/content.v1.json":s6},capabilities});
