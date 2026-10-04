// Compile the existing visual recipes; preserve the preview and dynamic task count.
const rows = $input.all();
if (rows.length !== 1) throw new Error('Visual compiler: expected one preview');
const preview = rows[0].json;
if (preview.schema !== 'writing_preview.v1' || preview.status !== 'draft'
    || preview.editing_status !== 'completed' || !preview.content_id
    || typeof preview.article_markdown !== 'string' || !preview.article_markdown.trim()
    || preview.publication?.state !== 'NOT_PUBLISHED') {
  throw new Error('Visual compiler: expected an edited, unpublished preview');
}
const emit = fields => [{json:{...preview,...fields},pairedItem:{item:0}}];
if (preview.visual_planning_status !== 'completed') {
  return emit({visual_compilation_status:'skipped',compiled_visual_plan:null});
}
// Existing recipes from V2 compiler v1. No article-specific content is added here.
const GLOBAL_INTEGRITY = [
  'Treat this as an editorial illustration, not documentary evidence.',
  'Do not invent identifiable people, organizations, military markings, vessel identity, product identity, locations, document contents, or real-world events beyond the supplied scene.',
  'Do not imply a stronger factual outcome, cause, certainty, or implementation status than the scene itself specifies.',
  'No readable words, letters, numbers, document text, labels, logos, signatures, watermarks, fake UI, charts, dashboards, or data overlays.',
  'Avoid generic AI imagery: no glowing brains, robot handshakes, neon circuitry, holographic data, floating interfaces, or unrelated cyberpunk scenery.'
].join(' ');
const ROLE_RECIPES = {
  article_cover: [
    'Compose this as a strong editorial cover image.',
    'Build one immediately readable focal relationship near the center.',
    'Keep the important subjects large enough to survive a small LinkedIn preview.',
    'Use supporting elements sparingly.',
    'Keep the outer edges comparatively quiet and preserve safe space for later cropping.',
    'Do not put the article title or any typography inside the artwork.'
  ].join(' '),
  body_illustration: [
    'Compose this as an editorial body illustration that clarifies one idea at a glance.',
    'Keep one dominant visual relationship and avoid unnecessary secondary props.',
    'The scene should remain understandable at mobile-feed size.',
    'Use negative space intentionally and avoid edge crowding.',
    'Do not turn the image into an infographic or labeled explainer.'
  ].join(' ')
};
const FORMAT_RECIPES = {
  linkedin_article_cover: [
    'Landscape composition intended for a 16:9 publication crop.',
    'Keep the focal subject and essential relationship inside the central safe region.'
  ].join(' '),
  inline_square: [
    'Square 1:1 composition.',
    'Use a compact central arrangement with generous surrounding breathing room.'
  ].join(' ')
};
const ARCHETYPES = {
  SATIRIST_PEN_INK: [
    'Editorial pen-and-ink illustration on warm ivory paper.',
    'Confident black contour lines, selective fine hatching, visible hand-drawn irregularity, and generous negative space.',
    'Use one restrained spot color only where it carries meaning.',
    'Favor an economical physical action or visual contradiction over decoration.',
    'Keep expressions and objects grounded rather than cartoonishly exaggerated.',
    'Sophisticated magazine-editorial tone: observant, intelligent, restrained, and concept-first.'
  ].join(' '),
  ABSTRACT_LINE_RISO: [
    'Abstract editorial line poster printed on warm uncoated fibrous paper.',
    'Use loose monoline contours, selective broken strokes, sparse hand hatching, and deliberate omission.',
    'One dominant ink color plus at most one small accent occupying a minor portion of the composition.',
    'Introduce subtle risograph or screen-print imperfections: uneven ink density, slight registration drift, and physical print texture.',
    'Maintain one compact visual cluster and a large connected field of negative space.',
    'Flat front-facing printed-art character rather than a framed mockup.'
  ].join(' '),
  HALFTONE_PAPER_COLLAGE: [
    'Contemporary magazine editorial paper collage.',
    'Use visibly illustrative black-and-white halftone cutout forms, tactile paper edges, restrained layering, and one strong flat color field.',
    'Allow subtle newsprint grain, slight torn-paper irregularity, thin ivory cut edges, and believable physical paper shadows.',
    'Keep the hierarchy simple: one dominant subject or relationship plus at most one supporting symbolic element.',
    'The collage must look intentionally constructed, not like authentic leaked photography or newspaper evidence.',
    'Avoid scrapbook clutter.'
  ].join(' '),
  HUMANIST_PAPERCRAFT: [
    'Tactile humanist editorial papercraft illustration.',
    'Use layered warm paper, visible fiber, cut and folded edges, sparse charcoal or ink marks, and soft physical shadows between layers.',
    'Favor human-scale gestures, access, labor, learning, or social consequence when they are present in the scene.',
    'Keep the forms sophisticated and restrained rather than cute or childlike.',
    'Natural warm ambient light and a calm magazine-editorial sensibility.'
  ].join(' '),
  DOCUMENTARY_REALISM: [
    'Grounded documentary-style synthetic editorial photography.',
    'Use believable practical materials, ordinary physical wear, natural imperfections, restrained real-world lighting, and an unpolished engineering or working-environment sensibility.',
    'Favor credible object placement and material behavior over cinematic spectacle.',
    'Use photographic realism only for generic environments and objects.',
    'Do not make the result resemble a recovered photograph of a specific reported event.',
    'Subtle film grain is acceptable; artificial drama is not.'
  ].join(' '),
  LUXURY_EDITORIAL: [
    'High-end technology-magazine editorial still life.',
    'Use disciplined premium composition, controlled dramatic lighting, deep but restrained tonal contrast, and finely observed physical materials.',
    'Favor matte metal, paper, glass, stone, leather, or other materials only when appropriate to the supplied scene.',
    'Maintain large quiet fields and a single strong focal subject.',
    'The image should feel authoritative and expensive without becoming advertising.',
    'Avoid gratuitous product glamour.'
  ].join(' '),
  NEO_BRUTALIST: [
    'Neo-brutalist editorial illustration.',
    'Use a warm cream field, substantial imperfect black outlines, flat geometric shapes, hard-edged blocks, deliberate scale contrast, and one vivid accent color.',
    'Allow subtle halftone or print texture.',
    'Use only a few large visual elements and make their relationship immediately legible.',
    'The mood may be blunt, energetic, or slightly confrontational but not chaotic.',
    'Do not imitate software cards, dashboards, or interface components.'
  ].join(' '),
  MACRO_SILICON: [
    'High-detail macro editorial material study of silicon, semiconductor substrate, packaging, metal, or wafer-like structures as specified by the scene.',
    'Use physically credible microtexture, controlled reflective surfaces, shallow depth cues, and precise studio light.',
    'Favor material fascination over science-fiction glow.',
    'Do not invent readable die markings, process-node labels, company logos, circuit specifications, or microscopic technical text.',
    'Do not imply an exact real chip layout unless one is explicitly supplied.'
  ].join(' '),
  LINOCUT_EDITORIAL: [
    'Two-color linocut editorial print on warm fibrous cream paper.',
    'Use bold carved gouge marks, visible carving direction, uneven ink coverage, dry edges, chatter marks, simplified graphic masses, and slight registration mismatch between color passes.',
    'Use a deep black or indigo key plate with one restrained secondary ink such as muted vermilion, ochre, or cobalt.',
    'Strong light-dark separation should give the scene weight without turning it into propaganda or melodrama.',
    'No gradients or glossy digital rendering.'
  ].join(' '),
  DOUBLE_EXPOSURE: [
    'Minimal double-exposure editorial composition.',
    'Establish one unmistakable dominant subject and combine it with exactly one secondary environment, material, or mechanism only where the overlap communicates the supplied relationship.',
    'Use soft physical-looking overlap, restrained transparency, matte print character, subtle photographic grain, and a muted palette.',
    'Keep one clear silhouette or focal form and generous empty space.',
    'Avoid decorative particles, digital glow, HUD overlays, or arbitrary layered imagery.'
  ].join(' '),
  FINE_BITMAP_EDITORIAL: [
    'Contemporary fine-bitmap editorial poster.',
    'Use deliberate low-resolution pixel structure, ordered dithering, restricted bitmap shading, crisp silhouette hierarchy, and a limited three-to-five-color palette.',
    'Combine early-computing material language with sophisticated modern editorial composition.',
    'Allow subtle print or dot-matrix texture on a cream or muted paper-like field.',
    'This must not resemble videogame pixel art, a terminal screen, or nostalgic UI.'
  ].join(' '),
  EDITORIAL_DIORAMA: [
    'Tactile editorial miniature diorama photographed as a deliberately constructed conceptual scene.',
    'Build the scene from a very small number of handcrafted physical objects using matte paper, painted wood, clay, felt, cardboard, brushed metal, or other plausible miniature materials.',
    'Make scale, spacing, balance, obstruction, or contact between objects carry the meaning.',
    'Use soft controlled studio light, natural shallow depth cues, subtle handmade imperfections, and a neutral warm background.',
    'The construction should look intelligent and editorial rather than toy-like.',
    'Avoid cute mascot faces, glossy plastic, miniature labels, model-railway clutter, or whimsical props that dilute the central relationship.'
  ].join(' '),
  RETRO_FUTURIST: [
    'Editorial retro-futurist illustration using historically inflected speculative design language.',
    'Use restrained vintage print texture, geometric industrial forms, period-appropriate graphic simplification, and a limited analog palette.',
    'The scene should feel like a past vision of technology rather than generic nostalgia.',
    'Do not imply that speculative devices were real products or documented events.',
    'Avoid neon cyberpunk reinterpretation.'
  ].join(' '),
  PASTORAL_ANIMATION: [
    'Hand-painted pastoral animation-style editorial illustration.',
    'Use organic line work, soft cel-like shading, luminous natural light, atmospheric depth, painterly vegetation or environment only where relevant, and a calm handcrafted surface.',
    'Favor human-scale aspiration, learning, creativity, or nature-technology relationships.',
    'Keep the visual language original and general rather than imitating a named artist, studio, film, or recognizable composition.',
    'Avoid decorative scenic beauty that does not support the supplied scene.'
  ].join(' '),
  ABSTRACT_FINE_ART: [
    'Controlled abstract fine-art editorial composition.',
    'Translate the supplied relationship into clearly organized material tension, weight, geometry, surface, rhythm, or spatial opposition.',
    'Use restrained gallery-like composition and sophisticated material variation.',
    'The abstract relationship must remain visually intelligible without explanatory typography.',
    'Avoid generic liquid metal, glowing crystals, volumetric fog, decorative particles, or arbitrary surrealism.'
  ].join(' ')
};
try {
  const input = preview.visual_plan;
  if (input?.schema !== 'visual_plan_validated.v1' || input.status !== 'PASS'
      || input.final_article !== preview.article_markdown
      || !Array.isArray(input.images_to_generate) || !input.images_to_generate.length) {
    throw new Error('invalid_visual_plan');
  }
  const compiled = input.images_to_generate.map((task,i)=>{
    const required = ['id','role','visual_mode','archetype_id','format_preset','purpose','scene','alt_text'];
    if (!task || required.some(k=>typeof task[k] !== 'string' || !task[k].trim())
        || typeof task.caption !== 'string' || !task.placement || typeof task.placement.anchor !== 'string'
        || task.id !== (i ? 'IMG_'+i : 'COVER_IMG') || task.visual_mode !== 'editorial_image'
        || task.role !== (i ? 'body_illustration' : 'article_cover')
        || task.format_preset !== (i ? 'inline_square' : 'linkedin_article_cover')
        || !Object.hasOwn(ARCHETYPES,task.archetype_id)) throw new Error('invalid_visual_task');
    const prompt = ['EDITORIAL SCENE:',task.scene.trim(),'',
      'VISUAL ARCHETYPE:',ARCHETYPES[task.archetype_id],'',
      'COMPOSITION:',ROLE_RECIPES[task.role],FORMAT_RECIPES[task.format_preset],'',
      'INTEGRITY AND EXCLUSIONS:',GLOBAL_INTEGRITY].join('\n');
    return {...task,prompt};
  });
  const archetypes = [...new Set(compiled.map(t=>t.archetype_id))];
  return emit({visual_compilation_status:'completed',compiled_visual_plan:{
    schema:'visual_prompt_compiled.v1',status:'PASS',source_plan_schema:input.source_plan_schema,
    final_article:input.final_article,cover_image:compiled[0],body_images:compiled.slice(1),
    images_to_generate:compiled,counts:{total:compiled.length,cover:1,body:compiled.length-1,archetypes:archetypes.length},
    archetypes_used:archetypes
  }});
} catch (error) {
  return emit({visual_compilation_status:'failed',compiled_visual_plan:null,
    warnings:[...(preview.warnings||[]),'visual_compilation_failed']});
}
