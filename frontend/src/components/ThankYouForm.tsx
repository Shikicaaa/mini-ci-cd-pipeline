import Navbar from './Navbar'

const ThankYouForm = () => {
  return (
    <div className='flex flex-col min-h-screen bg-gray-900 text-gray-100'>
        <Navbar />
        <div className ="flex-grow px-6 py-48 max-w-4xl mx-auto flex flex-col items-center justify-center">
            <h1 className='text-3xl font-bold mb-6'>Thank you for installing this application</h1>
            <p className='text-3xl'>If you need help or bugs happen feel free to reach out to me.</p>
            <p className='text-2xl mt-5 text-cyan-300'>Discord: stenezmaja</p>
        </div>
    </div>
  )
}

export default ThankYouForm