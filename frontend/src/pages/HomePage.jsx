import { images } from "../assets/images";
import Header from "../components/Header/Header";
import HeroSection from "../components/HeroSection/HeroSection";
import MediaSection from "../components/MediaSection/MediaSection";
import "./HomePage.css";

function HomePage() {
  const services = [
    {
      id: 1,
      number: "01",
      title: "ЗОВНІШНЯ РЕКЛАМА",
      label: "OOH",
      image: images.oohImage,
      description: "Білборди та рекламні конструкції для розміщення зовнішньої реклами.",
    },
    {
      id: 2,
      number: "02",
      title: "ЦИФРОВА ЗОВНІШНЯ РЕКЛАМА",
      label: "DOOH",
      image: images.doohImage,
      description: "LED-екрани для динамічного рекламного контенту.",
    },
    {
      id: 3,
      number: "03",
      title: "ДРУК",
      label: "PRINT",
      image: images.printImage,
      description: "Друкована продукція для бізнесу, подій та рекламних кампаній.",
    },
  ];

  return (
    <div className="home-page">
      <Header />
      <main>
        <HeroSection />
        <MediaSection services={services} />
      </main>
    </div>
  );
}

export default HomePage;