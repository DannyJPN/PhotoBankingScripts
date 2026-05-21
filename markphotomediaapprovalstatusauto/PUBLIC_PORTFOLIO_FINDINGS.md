# Public Portfolio Findings

This file captures concrete read-only samples gathered during investigation of the public portfolio crawler.

These are not current matcher approvals.
They are manually sampled candidate pairs showing that the portfolio crawler can see likely corresponding assets on the photobank while the current CSV matching still fails.

## ShutterStock

- CSV file: `DSC00926.JPG`
- Photobank URL: `https://www.shutterstock.com/cs/image-photo/centered-close-oxeye-daisy-leucanthemum-vulgare-2730429521`
- CSV description: `Macro of oxeye daisy (Leucanthemum vulgare) with white petals and golden disc, photographed at ground level in a summer meadow. Warm late-afternoon light and shallow depth blur tall grasses.`
- Photobank title: `Centrovaný detail oxeye sedmikrásky (Leucanthemum vulgare) s bílými paprsky a žlutým kotoučem, nastavený proti zelené louce listí v měkkém denním světle a mělké hloubce pole.`

## AdobeStock

- CSV file: `DSC01525.JPG`
- Photobank URL: `https://stock.adobe.com/cz/images/cluster-of-purple-crocus-flowers-with-yellow-stamens-blooming-on-a-sunlit-urban-lawn-heralding-early-spring/1859773274`
- CSV description: `Top-down close-up of striped purple-and-white Crocus vernus with bright orange stigmas blooming in sunlit lawn, surrounded by green grass and yellow daffodil buds and flowers. Vibrant spring scene.`
- Photobank title: `Cluster of purple crocus flowers with yellow stamens blooming on a sunlit urban lawn, heralding early spring.`

## Dreamstime

- CSV file: `DSC01521.JPG`
- Photobank URL: `https://www.dreamstime.com/spring-crocus-blossom-close-up-vivid-purple-petals-orange-stigma-two-flowers-grassy-temperate-meadow-perspective-image431395777`
- CSV description: `Overhead close-up of Crocus vernus blooms with purple-and-white striped petals and vivid orange stigmas on a grassy lawn, with a yellow daffodil nearby, in bright spring sunlight.`
- Photobank title: `Spring crocus blossom close up with vivid purple petals and orange stigma royalty free`

## DepositPhotos

- CSV file: `DSC00919.JPG`
- Photobank URL: `https://depositphotos.com/photo/close-highbush-blueberry-vaccinium-corymbosum-862278628.html`
- CSV description: `Close-up of a highbush blueberry (Vaccinium corymbosum) with green, unripe clusters among glossy leaves, growing in dry straw mulch under bright midday sun in a home garden during summer.`
- Photobank title: `Close highbush blueberry vaccinium corymbosum`

## Pond5

- CSV file: `DSC01524.JPG`
- Photobank URL: `https://www.pond5.com/stock-images/photos/item/324972316-single-red-tulip-top-down-view-grassy-lawn-spring-sunlight`
- CSV description: `Top-down close-up of a single red and orange tulip with yellow center lying on green spring lawn, surrounded by mixed fresh and dry grass blades under bright sunlight.`
- Photobank title: `Single Red Tulip Top-Down View On Grassy Lawn In Spring Sunlight`

## GettyImages

- CSV file: `DSC01521.JPG`
- Photobank URL: `https://www.istockphoto.com/en/photo/spring-crocus-with-purple-striped-petals-close-up-in-garden-sunlight-gm2257113803`
- CSV description: `Overhead close-up of Crocus vernus blooms with purple-and-white striped petals and vivid orange stigmas on a grassy lawn, with a yellow daffodil nearby, in bright spring sunlight.`
- Photobank title: `Spring crocus with purple striped petals close up in garden sunlight`

## Summary

- The crawler now reaches and extracts public portfolio assets for the supported searchable banks.
- The remaining blocker is CSV matching, because checked rows use `Popis` while `Název` is empty for the relevant records.
- The pairs above are meant for manual inspection on another machine.
