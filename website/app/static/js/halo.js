const HaloImage = document.querySelector('.halo-image');

if (HaloImage) {
    const haloLeftOffset = Math.random() * 30 + 20;

    HaloImage.style.left = `${haloLeftOffset}px`;
}