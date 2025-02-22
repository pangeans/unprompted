import Image from 'next/image';

interface ImageSectionProps {
  image: string | null;
}

export const ImageSection: React.FC<ImageSectionProps> = ({ image }) => (
  <div className="mb-4">
    {image && (
      <Image
        src={image}
        alt="Guess the Prompt!"
        width={300}
        height={300}
      />
    )}
  </div>
);